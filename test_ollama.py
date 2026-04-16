# test_ollama.py
import requests
import json

print("Testing Ollama connection...")
print("=" * 50)

try:
    # Check if Ollama is running
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        print(f"✅ Ollama is running!")
        print(f"📦 Available models:")
        for model in models:
            print(f"   - {model.get('name', 'unknown')}")
        print("=" * 50)
        
        # Test with first model
        if models:
            model_name = models[0].get('name')
            print(f"\n🧪 Testing with model: {model_name}")
            print("-" * 50)
            
            test_prompt = "Say 'Hello from MFASHA AI!' in one sentence."
            
            response = requests.post('http://localhost:11434/api/generate',
                                    json={
                                        'model': model_name,
                                        'prompt': test_prompt,
                                        'stream': False
                                    },
                                    timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json().get('response', 'No response')
                print(f"🤖 AI Response: {ai_response}")
                print("=" * 50)
                print("✅ Ollama is working perfectly!")
            else:
                print(f"❌ Error: Status {response.status_code}")
    else:
        print(f"❌ Ollama not responding. Status: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Ollama. Please make sure it's running.")
    print("\nTo start Ollama:")
    print("1. Open a new terminal")
    print("2. Run: ollama serve")
    print("3. Keep it running")
    print("4. Run this test again")
except Exception as e:
    print(f"❌ Error: {e}")