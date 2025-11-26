
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ks_infrastructure import ks_mysql
from ks_infrastructure.services.exceptions import KsConnectionError

def migrate_instructions():
    print("Migrating instructions from 'hu' to 'huxiaoxiao'...")
    
    conn = ks_mysql()
    cursor = conn.cursor()
    
    try:
        # Update owner from 'hu' to 'huxiaoxiao'
        sql = "UPDATE agent_instructions SET owner = 'huxiaoxiao' WHERE owner = 'hu'"
        cursor.execute(sql)
        conn.commit()
        
        print(f"Successfully migrated {cursor.rowcount} instructions.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error migrating instructions: {e}")
    finally:
        cursor.close()

if __name__ == "__main__":
    migrate_instructions()
