from dataclasses import dataclass

@dataclass
class AtcoderProblem:
    contestId: int
    problemId: str
    problemType: str
    rating: int | None = None

    @property
    def url(self):
        return f"https://atcoder.jp/contests/{self.contestId}/tasks/{self.problemId}"

    def __str__(self):
        return f"{self.problemId}"


import aiohttp
import asyncio
import time
api_lock = asyncio.Lock()
last_update = -1
cached_problems = []
async def fetch_all_problems():
    global last_update, cached_problems

    if time.time() - 3600 <= last_update:
        return cached_problems

    last_update = time.time()
    url = "https://kenkoooo.com/atcoder/resources/problem-models.json"
    async with api_lock:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        await asyncio.sleep(1)

    cached_problems.clear()
    def extract_contest_id(name):
        p = 0
        while p < len(name) and name[p] != '_':
            p += 1

        assert p < len(name), "Wtf is this problemId"
        p2 = p - 1
        while p2 > 0 and name[p2] >= '0' and name[p2] <= '9':
            p2 -= 1
        p2 += 1
        assert p2 > 0, "Wtf is this problemId"
        return name[0:p], name[0:p2]
            
    for problemId, problem in data.items():
        contestId, problemType = extract_contest_id(problemId)
        rating = problem.get("difficulty")
        if rating == None: #Deal with the case where we don't know the rating
            rating = 0
        cached_problems.append(AtcoderProblem(
            contestId = contestId,
            problemId = problemId,
            problemType = problemType,
            rating = rating
        ))

    return cached_problems

import random

async def recommend_problems_for_user(min_rating, max_rating, exclude_type, solved_problem = [], num_problem = 1):
    problems = await fetch_all_problems()
    exclude_type = set(exclude_type)
    solved_problem = set(solved_problem)
    available_problem = []
    for problem in problems:
        if problem.rating < min_rating:
            continue
        if problem.rating > max_rating:
            continue
        if problem.problemType in exclude_type:
            continue
        if problem.problemId in solved_problem:
            continue
        available_problem.append(problem)
    recommended_problems = random.sample(available_problem, k = num_problem)
    return recommended_problems
    