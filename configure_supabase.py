import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.cloud.supabase_service import SupabaseCloudService
import httpx

def main():
    print("=" * 70)
    print("  EduCloud: Supabase Cloud Automatic Configuration Wizard")
    print("=" * 70)
    print("This utility configures Supabase Cloud Object Storage & PostgreSQL")
    print("for your Cloud Assignment Submission & Feedback Portal.")
    print("=" * 70)
    print()

    # 1. Project URL
    default_url = os.getenv("SUPABASE_URL", "")
    url = input(f"Enter Supabase Project URL (e.g. https://xxxx.supabase.co) [{default_url}]: ").strip() or default_url

    if not url.startswith("http"):
        print("[ERROR] Invalid URL. Must start with https://")
        return

    # 2. API Key
    default_key = os.getenv("SUPABASE_KEY", "")
    key = input(f"Enter Supabase API Key (anon public key or service_role key) [{default_key}]: ").strip() or default_key

    if not key:
        print("[ERROR] API Key is required.")
        return

    # 3. Database URL (Optional)
    default_db = os.getenv("SUPABASE_DB_URL", "")
    db_url = input(f"Enter Supabase PostgreSQL Connection String (Optional, press Enter to keep SQLite) [{default_db}]: ").strip() or default_db

    # 4. Storage Bucket
    bucket = input("Enter Supabase Storage Bucket name [assignments]: ").strip() or "assignments"

    print("\n[INFO] Validating Supabase credentials...")
    test_service = SupabaseCloudService()
    test_service.url = url.rstrip("/")
    test_service.key = key
    test_service.bucket = bucket

    health = test_service.health_check()
    if health.get("status") == "connected":
        print(f"  [SUCCESS] Connected to Supabase Project: {url}")
        print(f"  [SUCCESS] Storage service active. Buckets found: {health.get('all_buckets')}")
        if not health.get("bucket_exists"):
            print(f"  [NOTICE] Bucket '{bucket}' was not found in your Supabase project.")
            print(f"           Attempting to create bucket '{bucket}' automatically...")
            try:
                endpoint = f"{url.rstrip('/')}/storage/v1/bucket"
                headers = test_service._headers(content_type="application/json")
                resp = httpx.post(endpoint, json={"id": bucket, "name": bucket, "public": True}, headers=headers, timeout=10.0)
                if resp.status_code in (200, 201):
                    print(f"  [SUCCESS] Bucket '{bucket}' created successfully!")
                else:
                    print(f"  [WARNING] Could not auto-create bucket: {resp.text}")
                    print(f"            Please ensure bucket '{bucket}' is created in Supabase Dashboard -> Storage.")
            except Exception as e:
                print(f"  [WARNING] Error auto-creating bucket: {e}")
    else:
        print(f"  [WARNING] Connection check reported: {health}")
        print("            We will still write the configuration to your .env file.")

    # 5. Write to .env
    env_path = BASE_DIR / ".env"
    existing_lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    # Filter out existing supabase entries
    new_lines = []
    for line in existing_lines:
        if not any(line.startswith(k) for k in ["SUPABASE_URL=", "SUPABASE_KEY=", "SUPABASE_DB_URL=", "SUPABASE_STORAGE_BUCKET=", "STORAGE_DRIVER="]):
            new_lines.append(line)

    new_lines.append("\n# Supabase Cloud Configuration\n")
    new_lines.append(f"SUPABASE_URL={url}\n")
    new_lines.append(f"SUPABASE_KEY={key}\n")
    new_lines.append(f"SUPABASE_STORAGE_BUCKET={bucket}\n")
    new_lines.append("STORAGE_DRIVER=supabase\n")
    if db_url:
        new_lines.append(f"SUPABASE_DB_URL={db_url}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"\n[SUCCESS] Configuration saved to {env_path.name}!")
    print("\nNext steps:")
    print("1. Apply database schema in Supabase SQL editor: paste 'supabase_schema.sql'")
    print("2. Run server: python main.py")
    print("3. Check health: http://127.0.0.1:8000/api/health")

if __name__ == "__main__":
    main()
