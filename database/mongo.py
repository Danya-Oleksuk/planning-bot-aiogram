import pymongo

from config import MONGO_API_TOKEN


async def create_mongo_database():
    main_client = pymongo.AsyncMongoClient(MONGO_API_TOKEN)
    db = main_client["tasks_database"]

    tasks_collection = db["tasks"]

    return tasks_collection, db


class TaskRepository:
    def __init__(self, tasks_collection, db):
        self.tasks_collection = tasks_collection
        self.db = db

    async def create_task(self, user_id: int, task_description: str):
        if self.tasks_collection is not None:
            task = {"user_id": user_id, "task": task_description, "status": "❌"}
            await self.tasks_collection.insert_one(task)

    async def fetch_tasks(self, user_id: int):
        lst = []

        async for data in self.tasks_collection.find({"user_id": user_id}):
            lst.append({data.get("task"): data.get("status")})
        return lst

    async def fetch_all_tasks(
        self,
    ):
        lst = []

        async for data in self.tasks_collection.find():
            lst.append(
                f"{data.get('user_id')} - {data.get('task')} - {data.get('status')}"
            )
        return lst

    async def count_user_tasks(self, user_id: int):
        return await self.tasks_collection.count_documents({"user_id": user_id})

    async def get_user_task_status(self, user_id: int):
        data = await self.tasks_collection.find_one({"user_id": user_id})
        return data.get("status")

    async def mark_task_completed(self, user_id, task_number):
        if not await self.fetch_tasks(user_id):
            return False

        task_cursor = self.tasks_collection.find({"user_id": user_id}).sort(
            [("_id", 1)]
        )

        tasks_list = []
        async for task in task_cursor:
            tasks_list.append(task)

        if task_number > len(tasks_list):
            return False

        task_to_update = tasks_list[task_number - 1]

        await self.db.tasks.update_one(
            {"_id": task_to_update["_id"]}, {"$set": {"status": "✅"}}
        )
        return True

    async def delete_task_by_index(self, number_of_task: int, user_id: int):
        if not await self.fetch_tasks(user_id):
            return False

        tasks = self.tasks_collection.find({"user_id": user_id})
        tasks_list = [task async for task in tasks]

        if number_of_task - 1 < len(tasks_list):
            task_to_delete = tasks_list[number_of_task - 1]

            await self.tasks_collection.delete_one(
                {
                    "user_id": user_id,
                    "task": task_to_delete.get("task"),
                    "status": task_to_delete.get("status"),
                }
            )
            return True
        else:
            return False

    async def delete_all_tasks(self, user_id: int):
        if not await self.fetch_tasks(user_id):
            return False

        await self.tasks_collection.delete_many({"user_id": user_id})
        return True
