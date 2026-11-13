
const API_URL = "http://127.0.0.1:8000";

let apiKey = localStorage.getItem("chat_api_key") || "";
let currentSessionId = null;
let activeController = null;


// DOM elements

const sessionList = document.getElementById("sessionList");
const messages = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");

const sendBtn = document.getElementById("sendBtn");
const stopBtn = document.getElementById("stopBtn");

const loading = document.getElementById("loading");
const errorMessage = document.getElementById("errorMessage");
const status = document.getElementById("status");


// API helper

async function apiRequest(path, options = {}) {

    const response = await fetch(API_URL + path, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "x-api-key": apiKey,
            ...options.headers
        }
    });

    if (!response.ok) {
        const error = await response.json();

        const err = new Error(
            error.detail || "Request failed"
        );

        err.status = response.status;
        err.retryAfter = response.headers.get("Retry-After");

        throw err;
    }

    return response;
}


// Save API key

document.getElementById("saveKeyBtn").onclick = () => {

    const value = document.getElementById("apiKey").value.trim();

    if (!value) {
        showError("Please enter your API key.");
        return;
    }

    apiKey = value;

    localStorage.setItem("chat_api_key", apiKey);

    document.getElementById("apiKey").value = "";

    document.getElementById("keyStatus").textContent =
        "API key saved.";

    errorMessage.textContent = "";
};


// Display errors

function showError(message) {
    errorMessage.textContent = message;
}


// Add message to UI

function addMessage(role, content = "") {

    const welcome = messages.querySelector(".welcome");

    if (welcome) {
        welcome.remove();
    }

    const element = document.createElement("div");

    element.className = `message ${role}`;

    const heading = document.createElement("strong");

    heading.textContent =
        role === "user" ? "You" : "AI Assistant";

    const text = document.createElement("div");

    text.className = "message-content";
    text.textContent = content;

    element.appendChild(heading);
    element.appendChild(text);

    messages.appendChild(element);

    messages.scrollTop = messages.scrollHeight;

    return text;
}


// Create new session

async function createSession() {

    try {

        const response = await apiRequest("/sessions", {
            method: "POST"
        });

        const data = await response.json();

        currentSessionId = data.id;

        messages.innerHTML = "";

        await loadSessions();

        status.textContent = "New session created";

    } catch (error) {

        showError(error.message);
    }
}


// Load all sessions

async function loadSessions() {

    try {

        const response = await apiRequest("/sessions");

        const sessions = await response.json();

        sessionList.innerHTML = "";

        sessions.forEach(session => {

            const item = document.createElement("div");

            item.className = "session-item";

            if (session.id === currentSessionId) {
                item.classList.add("active");
            }

            item.textContent =
                "Chat " + session.id.slice(0, 8);

            item.onclick = () => openSession(session.id);

            sessionList.appendChild(item);

        });

    } catch (error) {

        showError(error.message);
    }
}


// Load previous messages

async function openSession(sessionId) {

    try {

        currentSessionId = sessionId;

        const response = await apiRequest(
            `/sessions/${sessionId}/messages`
        );

        const data = await response.json();

        messages.innerHTML = "";

        data.messages.forEach(message => {

            addMessage(
                message.role,
                message.content
            );

        });

        await loadSessions();

        status.textContent = "History loaded";

    } catch (error) {

        showError(error.message);
    }
}


// Handle chat streaming

async function sendMessage() {

    const text = messageInput.value.trim();

    if (!text) return;

    if (!apiKey) {
        showError("Please save your API key first.");
        return;
    }

    if (activeController) return;

    errorMessage.textContent = "";

    try {

        if (!currentSessionId) {
            await createSession();
        }

        if (!currentSessionId) return;

        addMessage("user", text);

        messageInput.value = "";

        loading.classList.remove("hidden");
        stopBtn.classList.remove("hidden");

        sendBtn.disabled = true;

        status.textContent = "Generating...";

        activeController = new AbortController();

        const response = await fetch(
            `${API_URL}/sessions/${currentSessionId}/chat`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "x-api-key": apiKey
                },

                body: JSON.stringify({
                    message: text
                }),

                signal: activeController.signal
            }
        );

        if (!response.ok) {

            let error;

            try {
                error = await response.json();
            } catch {
                error = {};
            }

            if (response.status === 429) {

                throw new Error(
                    `Rate limit exceeded. Retry after ${
                        response.headers.get("Retry-After") || "3600"
                    } seconds.`
                );
            }

            throw new Error(
                error.detail || "Chat request failed: " + response.status
            );
        }

        if (!response.body) {
            throw new Error("Streaming response is unavailable.");
        }

        const reader = response.body.getReader();

        const decoder = new TextDecoder();

        let buffer = "";
        let assistantElement = null;
        let receivedDone = false;

        while (true) {

            const { value, done } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, {
                stream: true
            });

            const events = buffer.split("\n\n");

            buffer = events.pop();

            for (const event of events) {

                const line = event
                    .split("\n")
                    .find(item => item.startsWith("data: "));

                if (!line) continue;

                const payload = JSON.parse(
                    line.substring(6)
                );

                if (payload.type === "token") {

                    if (!assistantElement) {
                        assistantElement = addMessage(
                            "assistant",
                            ""
                        );
                    }

                    assistantElement.textContent +=
                        payload.content;

                    messages.scrollTop = messages.scrollHeight;
                }

                if (payload.type === "done") {

                    receivedDone = true;

                    status.textContent =
                        `Completed | ${payload.total_tokens} tokens`;

                    console.log("Usage report:", payload);
                }

                if (payload.type === "error") {
                    throw new Error(payload.message);
                }
            }
        }

        if (!receivedDone) {
            status.textContent = "Stream ended";
        }

        if (assistantElement) {
            await loadSessions();
        }

    } catch (error) {

        if (error.name === "AbortError") {

            status.textContent = "Generation stopped";

        } else {

            showError(error.message);
            status.textContent = "Error";
        }

    } finally {

        activeController = null;

        loading.classList.add("hidden");
        stopBtn.classList.add("hidden");

        sendBtn.disabled = false;

    }
}


// Stop generation

stopBtn.onclick = () => {

    if (activeController) {
        activeController.abort();
    }

};


// Buttons

sendBtn.onclick = sendMessage;

document.getElementById("newChatBtn").onclick =
    createSession;


// Enter to send, Shift+Enter for new line

messageInput.addEventListener("keydown", event => {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }

});


// Initial application setup

document.getElementById("keyStatus").textContent =
    apiKey ? "API key loaded." : "API key not configured.";

loadSessions();
