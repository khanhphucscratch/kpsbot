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

async def get_user_info(handle):
    url = "https://codeforces.com/api/user.info"

    params = {
        "handles": handle
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params = params) as response:
            data = await response.json()
    await asyncio.sleep(2)
    return data

async def verifying_account(handle, time_left, time_right):
    url = "https://codeforces.com/api/user.status"
    params = {
        "handle": handle,
        "from": 1,
        "count": 10
    }

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

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params = params) as response:
            data = await response.json()
    problem_list = set() #Contain (contestid, problemid)
    for status in data["result"]:
        if status["verdict"] != "OK":
            continue
        problem_list.add((status["problem"]["contestId"], status["problem"]["index"]))

    await asyncio.sleep(2)
    return problem_list


async def get_all_problems(min_rating, max_rating, non_rating = False):
    url = "https://codeforces.com/api/problemset.problems"
    params = {}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params = params) as response:
            data = await response.json()

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
            tags = problem["tags"]
        ))
    return problem_list

import random
async def recommend_problems_for_user(handle_list, min_rating, max_rating, num_problem = 1):
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