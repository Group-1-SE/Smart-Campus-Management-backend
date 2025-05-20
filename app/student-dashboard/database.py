from supabase import create_client, Client
from config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Generic CRUD Operations
async def create_record(table: str, data: dict):
    try:
        response = supabase.table(table).insert(data).execute()
        return response.data
    except Exception as e:
        print(f"[CREATE] Error in '{table}': {e}")
        return None

async def read_records(table: str, filters: dict = None):
    try:
        query = supabase.table(table).select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"[READ] Error in '{table}': {e}")
        return None

async def update_record(table: str, filters: dict, updates: dict):
    try:
        query = supabase.table(table)
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.update(updates).execute()
        return response.data
    except Exception as e:
        print(f"[UPDATE] Error in '{table}': {e}")
        return None

async def delete_record(table: str, filters: dict):
    try:
        query = supabase.table(table)
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.delete().execute()
        return response.data
    except Exception as e:
        print(f"[DELETE] Error in '{table}': {e}")
        return None