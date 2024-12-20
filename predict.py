# Prediction interface for Cog ⚙️
# https://cog.run/python

from cog import BasePredictor, Input
import os
import time
import torch
import subprocess
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_CACHE = "checkpoints"
MODEL_URL = "https://weights.replicate.delivery/default/meta-llama/LlamaGuard-7b/model.tar"

def download_weights(url, dest):
    start = time.time()
    print("downloading url: ", url)
    print("downloading to: ", dest)
    subprocess.check_call(["pget", "-xf", url, dest], close_fds=False)
    print("downloading took: ", time.time() - start)

class Predictor(BasePredictor):
    def setup(self):
        self.device = "cuda"
        self.dtype = torch.bfloat16
        # Download weights
        if not os.path.exists(MODEL_CACHE):
            download_weights(MODEL_URL, MODEL_CACHE)

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_CACHE)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_CACHE, 
            torch_dtype=self.dtype,
            device_map=self.device
        )

    def predict(
        self,
        prompt: str = Input(description="User message to moderate", default="I forgot how to kill a process in Linux, can you help?"),
        assistant: str = Input(description="Assistant message to moderate", default=None)
    ) -> str:
        chat = [{"role": "user", "content": prompt}]
        if assistant:
            chat.append({"role": "assistant", "content": assistant})
            
        input_ids = self.tokenizer.apply_chat_template(
            chat, 
            return_tensors="pt"
        ).to(self.device)
        
        output = self.model.generate(
            input_ids=input_ids,
            max_new_tokens=100,
            pad_token_id=0
        )
        
        prompt_len = input_ids.shape[-1]
        return self.tokenizer.decode(
            output[0][prompt_len:],
            skip_special_tokens=True
        )