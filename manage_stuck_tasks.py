#!/usr/bin/env python3
"""
Comprehensive stuck task management script.
"""
import sqlite3
import requests
from datetime import datetime, timedelta
import json
import time
from finance_tools.config import get_config

class StuckTaskManager:
    def __init__(self, db_path=None, api_url='http://localhost:8070'):
        if db_path is None:
            config = get_config()
            self.db_path = config.get_database_url().replace('sqlite:///', '')
        else:
            self.db_path = db_path
        self.api_url = api_url
        self.stuck_threshold = timedelta(minutes=30)
    
    def check_stuck_tasks(self):
        """Check for stuck tasks in database and system."""
        print("🔍 Stuck Task Detection Report")
        print("=" * 50)
        
        # Check database
        db_stuck = self._check_database_stuck_tasks()
        
        # Check system
        system_stuck = self._check_system_stuck_tasks()
        
        return {
            'database_stuck': db_stuck,
            'system_stuck': system_stuck,
            'total_stuck': len(db_stuck) + len(system_stuck)
        }
    
    def _check_database_stuck_tasks(self):
        """Check for stuck tasks in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT task_id, start_time, status, records_downloaded, total_records
            FROM download_history 
            WHERE status = 'running'
            ORDER BY start_time DESC
        """)
        
        stuck_tasks = []
        for task in cursor.fetchall():
            task_id, start_time, status, records_downloaded, total_records = task
            start_dt = datetime.fromisoformat(start_time)
            duration = datetime.now() - start_dt
            
            if duration > self.stuck_threshold:
                stuck_tasks.append({
                    'task_id': task_id,
                    'start_time': start_time,
                    'duration': duration,
                    'records_downloaded': records_downloaded,
                    'total_records': total_records,
                    'source': 'database'
                })
        
        conn.close()
        return stuck_tasks
    
    def _check_system_stuck_tasks(self):
        """Check for stuck tasks in system."""
        try:
            response = requests.get(f'{self.api_url}/api/database/download-progress')
            progress_data = response.json()
            
            if not progress_data.get('is_downloading'):
                return []
            
            start_time = progress_data.get('start_time')
            if not start_time:
                return []
            
            start_dt = datetime.fromisoformat(start_time)
            duration = datetime.now() - start_dt
            
            if duration > self.stuck_threshold:
                return [{
                    'task_id': progress_data.get('task_id'),
                    'start_time': start_time,
                    'duration': duration,
                    'records_downloaded': progress_data.get('records_downloaded', 0),
                    'total_records': progress_data.get('total_records', 0),
                    'progress': progress_data.get('progress', 0),
                    'status': progress_data.get('status'),
                    'source': 'system'
                }]
            
            return []
        except Exception as e:
            print(f"❌ Error checking system: {e}")
            return []
    
    def reset_stuck_tasks(self):
        """Reset stuck tasks by triggering the built-in reset mechanism."""
        print("\n🔄 Resetting stuck tasks...")
        
        try:
            # Try to start a new download - this will trigger stuck task detection
            response = requests.post(f'{self.api_url}/api/database/download', 
                                   json={
                                       "startDate": "2025-01-01", 
                                       "endDate": "2025-01-02", 
                                       "kind": "YAT", 
                                       "funds": []
                                   })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Reset triggered: {result.get('message')}")
                print(f"🆔 New Task ID: {result.get('task_id')}")
                return True
            else:
                print(f"❌ Reset failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error resetting tasks: {e}")
            return False
    
    def force_reset_database(self):
        """Force reset stuck tasks in database."""
        print("\n🔧 Force resetting database stuck tasks...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update stuck running tasks to failed
            cursor.execute("""
                UPDATE download_history 
                SET status = 'failed', 
                    error_message = 'Task reset due to timeout',
                    end_time = ?
                WHERE status = 'running' 
                AND start_time < ?
            """, (datetime.now().isoformat(), 
                  (datetime.now() - self.stuck_threshold).isoformat()))
            
            affected = cursor.rowcount
            conn.commit()
            
            print(f"✅ Reset {affected} stuck tasks in database")
            return affected > 0
            
        except Exception as e:
            print(f"❌ Error force resetting database: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def monitor_task(self, task_id, duration_minutes=5):
        """Monitor a specific task for a given duration."""
        print(f"\n👀 Monitoring task {task_id} for {duration_minutes} minutes...")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            try:
                response = requests.get(f'{self.api_url}/api/database/download-progress')
                data = response.json()
                
                if data.get('task_id') == task_id:
                    print(f"📊 Progress: {data.get('progress', 0)}% - {data.get('status', 'Unknown')}")
                    
                    if not data.get('is_downloading'):
                        print("✅ Task completed!")
                        return True
                else:
                    print("⚠️  Task not found in system")
                    return False
                    
            except Exception as e:
                print(f"❌ Error monitoring task: {e}")
                return False
            
            time.sleep(10)  # Check every 10 seconds
        
        print("⏰ Monitoring timeout reached")
        return False
    
    def get_task_details(self, task_id):
        """Get detailed information about a specific task."""
        print(f"\n📋 Task Details for {task_id}")
        print("-" * 30)
        
        # Check database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM download_history WHERE task_id = ?
        """, (task_id,))
        
        db_task = cursor.fetchone()
        if db_task:
            print("📊 Database Record:")
            print(f"  Status: {db_task[6]}")
            print(f"  Start Time: {db_task[7]}")
            print(f"  End Time: {db_task[8]}")
            print(f"  Records: {db_task[9]}/{db_task[10]}")
            print(f"  Error: {db_task[11]}")
        
        conn.close()
        
        # Check system
        try:
            response = requests.get(f'{self.api_url}/api/database/download-progress')
            data = response.json()
            
            if data.get('task_id') == task_id:
                print("\n🔄 System Status:")
                print(f"  Is Downloading: {data.get('is_downloading')}")
                print(f"  Progress: {data.get('progress', 0)}%")
                print(f"  Status: {data.get('status')}")
                print(f"  Records: {data.get('records_downloaded', 0)}/{data.get('total_records', 0)}")
            else:
                print("\n⚠️  Task not active in system")
                
        except Exception as e:
            print(f"❌ Error checking system: {e}")

def main():
    manager = StuckTaskManager()
    
    # Check for stuck tasks
    stuck_info = manager.check_stuck_tasks()
    
    if stuck_info['total_stuck'] > 0:
        print(f"\n🚨 Found {stuck_info['total_stuck']} stuck task(s)!")
        
        # Show stuck tasks
        for task in stuck_info['database_stuck']:
            print(f"  📋 DB: {task['task_id']} - Running for {task['duration']}")
        
        for task in stuck_info['system_stuck']:
            print(f"  🔄 SYS: {task['task_id']} - Running for {task['duration']}")
        
        # Ask for action
        print("\n🛠️  Available actions:")
        print("1. Reset stuck tasks (automatic)")
        print("2. Force reset database")
        print("3. Monitor specific task")
        print("4. Get task details")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            manager.reset_stuck_tasks()
        elif choice == '2':
            manager.force_reset_database()
        elif choice == '3':
            task_id = input("Enter task ID to monitor: ").strip()
            duration = int(input("Monitor duration (minutes): ") or "5")
            manager.monitor_task(task_id, duration)
        elif choice == '4':
            task_id = input("Enter task ID for details: ").strip()
            manager.get_task_details(task_id)
    else:
        print("✅ No stuck tasks found!")

if __name__ == "__main__":
    main()
