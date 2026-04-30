#LLM Wrapper for ATLASS to reason and summarise

# from transformers import pipeline

# class LLMEngine:
# 	def __init__(self):
# 		# out model object to pass prompt
# 		self.generator = pipeline("text2text-generation",model="google/flan-t5-base", max_new_tokens=256)
	
# 	def generate(self, prompt):
# 		response = self.generator(prompt)
# 		return response[0]["generated_text"]

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class LLMEngine:
	def __init__(self):
		self.tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
		self.model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")

		self.device = "cuda" if torch.cuda.is_available() else "cpu"
		self.model.to(self.device)
	
	def generate(self, prompt):
		inputs = self.tokenizer(
			prompt,
			return_tensors = "pt",
			truncation = True,
			max_length = 512
		).to(self.device)

		outputs = self.model.generate(
			**inputs, 
			max_new_tokens=200,
			temperature = 0.2,
			do_sample = False,
			repetition_penalty = 1.5,
			min_length=50,
			no_repeat_ngram_size=3
		)
		
		answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
		# Remove duplicate sentences
		sentences = list(dict.fromkeys(answer.split(". ")))
		answer = ". ".join(sentences)
		# Fix formatting
		answer = answer.strip()

		return answer