import os
import onnxruntime_genai as og
from config.settings import settings

class SystemInferenceEngine:
    def __init__(self):
        self.model_dir = settings.MODEL_DIR
        
        if not os.path.exists(self.model_dir):
            raise RuntimeError(f"Engine Initialization Failure: Model directory missing at {self.model_dir}")
            
        print(f"Loading Quantized Graph into Memory from {self.model_dir}...")
        
        self.model = og.Model(self.model_dir)
        self.tokenizer = og.Tokenizer(self.model)
        print("ONNX Tensor Graph successfully mounted.")

    def stream_telemetry_log(self, error_log: str, context: str = None):
        """
        Yields tokens one by one as they are computed on the silicon.
        """
        system_prompt = (
            "You are an expert Backend Systems Diagnostic Engineer specializing in payment infrastructure. "
            "Analyze the incoming raw error log. Provide a direct, 2-sentence response identifying "
            "the error source and the direct remedy steps. Be highly concise."
        )
        user_prompt = f"Error Log: {error_log}\nContext: {context if context else 'Dev Profile'}"
        formatted_prompt = f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{user_prompt}<|end|>\n<|assistant|>\n"
        
        tokens = self.tokenizer.encode(formatted_prompt)
        params = og.GeneratorParams(self.model)
        # 💡 CRITICAL: Lower max_length cuts down processing time drastically!
        params.set_search_options(max_length=settings.MAX_TOKENS, temperature=settings.TEMPERATURE, top_p=settings.TOP_P)
        params.input_ids = tokens
        
        generator = og.Generator(self.model, params)
        tokenizer_stream = self.tokenizer.create_stream()
        
        while not generator.is_done():
            generator.compute_logits()
            generator.generate_next_token()
            new_token = generator.get_next_tokens()[0]
            decoded_chunk = tokenizer_stream.decode(new_token)
            
            # Yield the string chunk instantly back to the FastAPI network connection layer
            yield decoded_chunk

# Instantiate as a singleton context to avoid reloading the heavy weights on every API request
engine = None

def get_inference_engine():
    global engine
    if engine is None:
        engine = SystemInferenceEngine()
    return engine