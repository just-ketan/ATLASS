import os
import sys

import torch

class LLMEngine:
	def __init__(self, model_name="google/flan-t5-large"):
		self.model_name = model_name
		self.tokenizer = None
		self.model = None
		self._load_failed = False
		self.device = "cuda" if torch.cuda.is_available() else "cpu"

	def _load_model(self):
		if self.model is not None or self._load_failed:
			return self.model is not None
		try:
			from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

			allow_download = os.environ.get("ATLASS_ALLOW_MODEL_DOWNLOAD") == "1"
			self.tokenizer = AutoTokenizer.from_pretrained(
				self.model_name,
				local_files_only=not allow_download,
			)
			self.model = AutoModelForSeq2SeqLM.from_pretrained(
				self.model_name,
				local_files_only=not allow_download,
			)
			self.model.to(self.device)
		except Exception as exc:
			self._load_failed = True
			print(f"[ATLASS] LLM unavailable; using retrieval-only answers ({exc}).", file=sys.stderr)
			return False
		return True
	
	def generate(self, prompt):
		if not self._load_model():
			return ""

		inputs = self.tokenizer(
			prompt,
			return_tensors = "pt",
			truncation = True,
			max_length = 512
		).to(self.device)

		outputs = self.model.generate(
			**inputs, 
			max_new_tokens=200,
			do_sample = False,
			repetition_penalty = 1.5,
			no_repeat_ngram_size=3
		)
		
		answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
		# Remove duplicate sentences
		sentences = list(dict.fromkeys(answer.split(". ")))
		answer = ". ".join(sentences)
		# Fix formatting
		answer = answer.strip()

		return answer
