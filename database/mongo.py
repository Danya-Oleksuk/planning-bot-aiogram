import pymongo

from config import MONGO_API_TOKEN


db = None
tasks_collection = None

async def create_mongo_database():
    global tasks_collection, db

    main_client = pymongo.AsyncMongoClient(MONGO_API_TOKEN)
    db = main_client['tasks_database']

    tasks_collection = db['tasks']

async def create_task(user_id: int, task_description: str):
    if tasks_collection is not None:
        task = {
            "user_id": user_id,
            "task": task_description,
            "status": "❌"
        }
        await tasks_collection.insert_one(task)

async def fetch_tasks(user_id: int):
    lst = []

    async for data in tasks_collection.find({"user_id": user_id}):
        lst.append({data.get("task"): data.get("status")})
    return lst

async def fetch_all_tasks():
    lst = []

    async for data in tasks_collection.find():
        lst.append(f"{data.get('user_id')} - {data.get('task')} - {data.get('status')}")
    return lst

async def count_user_tasks(user_id: int):
    return await tasks_collection.count_documents({"user_id": user_id})

async def get_user_task_status(user_id: int):
    data = await tasks_collection.find_one({"user_id": user_id})
    return data.get("status")

async def mark_task_completed(user_id, task_number):
    if not await fetch_tasks(user_id):
        return False

    task_cursor = tasks_collection.find({"user_id": user_id}).sort([("_id", 1)])

    tasks_list = []
    async for task in task_cursor:
        tasks_list.append(task)

    if task_number > len(tasks_list):
        return False

    task_to_update = tasks_list[task_number - 1]

    await db.tasks.update_one(
        {"_id": task_to_update["_id"]},
        {"$set": {"status": "✅"}}
    )
    return True

async def delete_task_by_index(number_of_task: int, user_id: int):
    if not await fetch_tasks(user_id):
        return False

    tasks = tasks_collection.find({"user_id": user_id})
    tasks_list = [task async for task in tasks]

    if number_of_task - 1 < len(tasks_list):
        task_to_delete = tasks_list[number_of_task - 1]

        await tasks_collection.delete_one({"user_id": user_id, "task": task_to_delete.get("task"), "status": task_to_delete.get("status")})
        return True
    else:
        return False

async def delete_all_tasks(user_id: int):
    if not await fetch_tasks(user_id):
        return False

    await tasks_collection.delete_many({"user_id": user_id})
    return True