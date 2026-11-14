from dataclasses import dataclass

@dataclass
class CodeforcesProblem:
    contestId: int
    index: str
    name: str
    rating: int | None = None
    tags: tuple[str, ...] = ()

    @property
    def url(self):
        return f"https://codeforces.com/problemset/problem/{self.contestId}/{self.index}"

    def __str__(self):
        return f"{self.contestId}{self.index} - {self.name}"


import aiohttp
import asyncio
import time
api_lock = asyncio.Lock()

async def get_user_info(handle):
    url = "https://codeforces.com/api/user.info"

    params = {
        "handles": handle
    }
    async with api_lock:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params = params) as response:
                data = await response.json()
        await asyncio.sleep(2)

    if data["status"] != "OK":
        raise RuntimeError(data.get("comment", "Codeforces API failed"))
    return data

async def verifying_account(handle, time_left, time_right):
    url = "https://codeforces.com/api/user.status"
    params = {
        "handle": handle,
        "from": 1,
        "count": 10
    }
    async with api_lock:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params = params) as response:
                data = await response.json()
        await asyncio.sleep(2)
    if data["status"] != "OK":
        return False
    for status in data["result"]:
        problem = status.get("problem", {})

        if (status.get("verdict") == "COMPILATION_ERROR"
            and problem.get("contestId") == 4
            and problem.get("index") == "A"
            and time_left <= status.get("creationTimeSeconds", 0) <= time_right):
            return True

    return False

import json
async def get_accepted_problem_from_user(handle):
    url = "https://codeforces.com/api/user.status"
    params = {
        "handle": handle
    }

    async with api_lock:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params = params) as response:
                data = await response.json()
        await asyncio.sleep(2)
    if data["status"] != "OK":
        raise RuntimeError(data.get("comment", "Codeforces API failed"))
    problem_list = set() #Contain (contestid, problemid)
    for status in data["result"]:
        if status.get("verdict") != "OK":
            continue

        problem = status.get("problem", {})

        if "contestId" not in problem or "index" not in problem:
            continue

        problem_list.add((
            problem["contestId"],
            problem["index"]
        ))

    return problem_list


data_caches = {}
last_updated_time = -1
async def get_all_problems(min_rating, max_rating, non_rating = False):
    global data_caches, last_updated_time
    if time.time() <= last_updated_time + 1800:
        data = data_caches
    else:
        async with api_lock:
            url = "https://codeforces.com/api/problemset.problems"
            params = {}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params = params) as response:
                    data = await response.json()
                    if data["status"] != "OK":
                        raise RuntimeError("Codeforces API failed")
                    data_caches = data
            
            last_updated_time = time.time()
            await asyncio.sleep(2)

    problem_list = [] #Contain (contestid, problemid)
    for problem in data["result"]["problems"]:
        if "rating" not in problem and non_rating == False:
            continue
        if "rating" in problem:
            rating = problem["rating"]
            if rating < min_rating or rating > max_rating:
                continue
        else:
            rating = 0
        problem_list.append(CodeforcesProblem(
            contestId = problem["contestId"],
            index = problem["index"],
            name = problem["name"],
            rating = rating,
            tags=tuple(problem["tags"])
        ))
    return problem_list

import random
async def recommend_problems_for_user(handle_list, min_rating, max_rating, minimum_id, num_problem = 1):
    #Return a list of CodeforcesProblem type struct
    all_problems = await get_all_problems(min_rating=min_rating, max_rating = max_rating)
    #Fetch all solved problems
    solved_problems = set()
    for handle in handle_list:
        problems = await get_accepted_problem_from_user(handle)
        for contest_id, problem_id in problems:
            solved_problems.add((contest_id, problem_id))
    #Take all unsolved problems
    all_unsolved_problems = [
        p for p in all_problems
        if (p.contestId, p.index) not in solved_problems
        and p.contestId >= minimum_id
    ]
    if len(all_unsolved_problems) < num_problem:
        return all_unsolved_problems

    recommended_problems = random.sample(all_unsolved_problems, k = num_problem)
    return recommended_problems

async def check_if_accepted(handle_list, problem):
    #problem = (contestId, index)
    for handle in handle_list:
        problems = await get_accepted_problem_from_user(handle)
        if problem in problems:
            return True
    return False



print(asyncio.run(check_if_accepted(["LovelyStar", "kodomo_tachim"], (2070, "F"))))