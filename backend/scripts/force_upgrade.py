
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(dotenv_path='backend/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") # Use Service Key for admin access

if not url or not key:
    print("Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(url, key)

EMAIL = 'aaditchandra2212@gmail.com'

def check_and_upgrade():
    # 1. Fetch user by email
    try:
        # We need to use the admin API to fetch user by email
        auth_users = supabase.auth.admin.list_users()
        target_user = next((u for u in auth_users if u.email == EMAIL), None)
        
        if not target_user:
            print(f"User {EMAIL} not found")
            return

        print(f"Found user: {target_user.id}")
        print(f"Current metadata: {target_user.user_metadata}")

        # 2. Update Auth Metadata
        new_metadata = target_user.user_metadata or {}
        new_metadata['plan'] = 'pro'
        new_metadata['user_type'] = 'student'
        
        supabase.auth.admin.update_user_by_id(
            target_user.id,
            attributes={'user_metadata': new_metadata}
        )
        print("Updated auth metadata to PRO")

        # 3. Update Profiles table
        # Check if row exists
        profile = supabase.table('profiles').select('*').eq('id', target_user.id).execute()
        if profile.data:
            supabase.table('profiles').update({'plan': 'pro'}).eq('id', target_user.id).execute()
            print("Updated profiles table to PRO")
        else:
            supabase.table('profiles').insert({'id': target_user.id, 'email': EMAIL, 'plan': 'pro', 'user_type': 'student'}).execute()
            print("Created profile entry as PRO")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_and_upgrade()
