import os
from openai import AzureOpenAI

endpoint = "https://ashenweerasinghe10-6492-resource.cognitiveservices.azure.com/"
model = os.getenv("AZURE_OPENAI_DEPLOYMENT")