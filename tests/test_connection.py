import ollama
response = ollama.chat(model='llama3.2', messages=[
  {'role': 'user', 'content': 'Are you working?'}
])
print(response['message']['content'])