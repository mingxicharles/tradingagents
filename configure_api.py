#!/usr/bin/env python3
"""
Interactive API configuration script
"""
import os
from pathlib import Path


def main():
    print("=" * 60)
    print("TradingAgents API Configuration")
    print("=" * 60)
    
    print("\nChoose your configuration:")
    print("1. Use OpenAI API (requires API key)")
    print("2. Use local Qwen model (no API key needed)")
    print("3. Check current configuration")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        configure_openai()
    elif choice == "2":
        configure_local_model()
    elif choice == "3":
        check_configuration()
    elif choice == "4":
        print("Exiting...")
        return
    else:
        print("Invalid choice")
        return


def configure_openai():
    """Configure OpenAI API"""
    print("\n" + "=" * 60)
    print("OpenAI API Configuration")
    print("=" * 60)
    
    print("\nGet your API key from: https://platform.openai.com/api-keys")
    api_key = input("\nEnter your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ No API key entered")
        return
    
    if len(api_key) < 20:
        print("⚠️  Warning: API key seems too short, but continuing...")
    
    # Option 1: Set for current session
    os.environ["OPENAI_API_KEY"] = api_key
    print(f"\n✓ API key set for current session (ends with ...{api_key[-4:]})")
    
    # Option 2: Save to .env file
    save_choice = input("\nSave to .env file for future use? (y/n): ").strip().lower()
    
    if save_choice == 'y':
        env_path = Path(".env")
        
        # Read existing .env content
        existing_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                existing_content = f.read()
        
        # Update or add API key
        lines = existing_content.split('\n')
        found = False
        new_lines = []
        
        for line in lines:
            if line.startswith('OPENAI_API_KEY='):
                new_lines.append(f'OPENAI_API_KEY={api_key}')
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f'OPENAI_API_KEY={api_key}')
        
        with open(env_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✓ Saved to {env_path}")
        print("\nTo use in future sessions:")
        print("  python-dotenv will auto-load from .env")
    
    print("\n" + "=" * 60)
    print("Configuration Complete!")
    print("=" * 60)
    print("\nYou can now run:")
    print("  python run.py AAPL --horizon 1w")


def configure_local_model():
    """Configure local model"""
    print("\n" + "=" * 60)
    print("Local Model Configuration")
    print("=" * 60)
    
    print("\nAvailable models:")
    print("1. Qwen/Qwen2.5-7B-Instruct (recommended, 8-12GB VRAM)")
    print("2. Qwen/Qwen2.5-1.5B-Instruct (low-end GPU/CPU)")
    print("3. Qwen/Qwen2.5-14B-Instruct (16-24GB VRAM)")
    print("4. Custom model")
    
    model_choice = input("\nEnter choice (1-4): ").strip()
    
    models = {
        "1": "Qwen/Qwen2.5-7B-Instruct",
        "2": "Qwen/Qwen2.5-1.5B-Instruct",
        "3": "Qwen/Qwen2.5-14B-Instruct",
    }
    
    if model_choice in models:
        model_name = models[model_choice]
    elif model_choice == "4":
        model_name = input("Enter HuggingFace model name: ").strip()
    else:
        print("Invalid choice")
        return
    
    # Set environment variables
    os.environ["USE_LOCAL_MODEL"] = "true"
    os.environ["LOCAL_MODEL"] = model_name
    
    print(f"\n✓ Configured to use local model: {model_name}")
    
    # Save to .env
    save_choice = input("\nSave to .env file for future use? (y/n): ").strip().lower()
    
    if save_choice == 'y':
        env_path = Path(".env")
        
        existing_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                existing_content = f.read()
        
        lines = existing_content.split('\n')
        new_lines = []
        found_use_local = False
        found_local_model = False
        
        for line in lines:
            if line.startswith('USE_LOCAL_MODEL='):
                new_lines.append('USE_LOCAL_MODEL=true')
                found_use_local = True
            elif line.startswith('LOCAL_MODEL='):
                new_lines.append(f'LOCAL_MODEL={model_name}')
                found_local_model = True
            else:
                new_lines.append(line)
        
        if not found_use_local:
            new_lines.append('USE_LOCAL_MODEL=true')
        if not found_local_model:
            new_lines.append(f'LOCAL_MODEL={model_name}')
        
        with open(env_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✓ Saved to {env_path}")
    
    print("\n" + "=" * 60)
    print("Configuration Complete!")
    print("=" * 60)
    print("\nFirst run will download the model (~15GB)")
    print("Run:")
    print("  python run.py AAPL --horizon 1w")


def check_configuration():
    """Check current configuration"""
    print("\n" + "=" * 60)
    print("Current Configuration")
    print("=" * 60)
    
    use_local = os.environ.get("USE_LOCAL_MODEL", "false").lower() == "true"
    
    if use_local:
        model = os.environ.get("LOCAL_MODEL", "Not set")
        print(f"\nMode: Local Model")
        print(f"Model: {model}")
        print(f"Status: ✓ Configured")
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            print(f"\nMode: OpenAI API")
            print(f"API Key: ...{api_key[-4:]}")
            print(f"Status: ✓ Configured")
        else:
            print(f"\nMode: OpenAI API")
            print(f"API Key: ❌ NOT SET")
            print(f"Status: ❌ Not configured")
    
    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        print(f"\n.env file: ✓ Found at {env_path}")
    else:
        print(f"\n.env file: ❌ Not found")
    
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled")

