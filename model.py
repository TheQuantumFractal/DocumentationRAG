import os
from modal import Image, Secret, Stub, method, web_endpoint
from fastapi import FastAPI, Request

MODEL_DIR = "/model"
BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

def download_model_to_folder():
    from huggingface_hub import snapshot_download

    os.makedirs(MODEL_DIR, exist_ok=True)

    snapshot_download(
        BASE_MODEL,
        local_dir=MODEL_DIR,
        token=os.environ["HUGGINGFACE_TOKEN"],
    )

image = (
    Image.from_registry("nvcr.io/nvidia/pytorch:22.12-py3")
    .pip_install(
        "torch==2.0.1+cu118", index_url="https://download.pytorch.org/whl/cu118"
    )
    # Pinned to 10/16/23
    .pip_install(
        "vllm @ git+https://github.com/vllm-project/vllm.git@651c614aa43e497a2e2aab473493ba295201ab20"
    )
    # Use the barebones hf-transfer package for maximum download speeds. No progress bar, but expect 700MB/s.
    .pip_install("hf-transfer~=0.1")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        download_model_to_folder,
        secret=Secret.from_name("huggingface"),
        timeout=60 * 20,
    )
)

stub = Stub("vllm-inference", image=image)

@stub.cls(gpu="A100", secret=Secret.from_name("huggingface"), timeout=60 * 5, container_idle_timeout=60 * 2)
class Model:
    def __enter__(self):
        from vllm import LLM

        # Load the model. Tip: MPT models may require `trust_remote_code=true`.
        self.llm = LLM(MODEL_DIR)

    @method()
    def generate(self, prompt: str):
        from vllm import SamplingParams

        sampling_params = SamplingParams(
            temperature=0.2,
            top_p=1,
            max_tokens=1200,
            presence_penalty=1.15,
        )
        result = self.llm.generate([prompt], sampling_params)
        return result[0].outputs[0].text

@stub.function(timeout=60 * 2)
@web_endpoint(method="POST")
async def web(request: Request):
    model = Model()
    question = (await request.json())["prompt"]
    return {"prompt": question + model.generate.remote(question)}

@stub.local_entrypoint()
def main():
    model = Model()
    question = "Implement a Python function to compute the Fibonacci numbers."
    print(model.generate.remote(question))