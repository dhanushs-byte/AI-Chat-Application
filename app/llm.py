
import os
import tiktoken

from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)
from dotenv import load_dotenv

load_dotenv()


# =====================================
# OpenRouter Configuration
# =====================================

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL")

if not API_KEY or API_KEY == "your_openrouter_api_key":
    raise RuntimeError("Configure OPENROUTER_API_KEY in .env")

if not MODEL or MODEL == "your_supported_model":
    raise RuntimeError("Configure OPENROUTER_MODEL in .env")


# =====================================
# Model Pricing (USD per million tokens)
# =====================================

INPUT_PRICE = float(
    os.getenv("INPUT_COST_PER_MILLION", "0")
)

OUTPUT_PRICE = float(
    os.getenv("OUTPUT_COST_PER_MILLION", "0")
)

if INPUT_PRICE < 0 or OUTPUT_PRICE < 0:
    raise ValueError("Model pricing cannot be negative")


# =====================================
# OpenRouter Client
# =====================================

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    max_retries=0,
    timeout=90
)


# =====================================
# Token Counting
# =====================================

def count_tokens(text: str) -> int:

    try:
        encoding = tiktoken.encoding_for_model(MODEL)

    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


# =====================================
# Calculate API Cost
# =====================================


def calculate_cost(input_tokens: int, output_tokens: int) -> float:

    input_price = float(
        os.getenv("INPUT_COST_PER_MILLION", "0")
    )

    output_price = float(
        os.getenv("OUTPUT_COST_PER_MILLION", "0")
    )

    input_cost = (
        input_tokens * input_price
    ) / 1_000_000

    output_cost = (
        output_tokens * output_price
    ) / 1_000_000

    total_cost = input_cost + output_cost

    print("Input price:", input_price)
    print("Output price:", output_price)
    print("Input tokens:", input_tokens)
    print("Output tokens:", output_tokens)
    print("Calculated cost:", total_cost)

    return round(total_cost, 10)



# =====================================
# Streaming LLM Response
# =====================================

@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(
        multiplier=1,
        max=10
    ),
    reraise=True
)
def create_stream(messages):

    return client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        stream_options={
            "include_usage": True
        }
    )


# =====================================
# Configuration Information
# =====================================

def get_model_config():

    return {
        "model": MODEL,
        "input_price_per_million": INPUT_PRICE,
        "output_price_per_million": OUTPUT_PRICE
    }
