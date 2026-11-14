Basically a bot that I decided to develop in my free time

It's made just for randomize Codeforces problem

New features (that I haven't see in any other bot):
 - can include many Codeforces handle for each users (useful for someone with many alts account like me hehe)
 - You could say Hello to anyone! (I coded that just to test if my bot can connect with Discord properly, because I'm new to this. But I decided to keep that anyway)

Sus thing:
 - I made this in a single morning, with no background knowledge, so I didn't have time to
 learn fancy thing such as LiteSQL. So if I refresh my bot, all the data will be lost immediately
 I combat this partially with /backup and /load_backup, two admin-only comment that will 
 backup handle lists for all users. Everything else (training progress, etc) is loss (I mean, I could backup that too, but I'm too lazy to implement that hehe)
 - This bot has a security flaw: If a user verify a handle, but then cannot verify that handle, and they don't comment /verify again, that handle will be lost (no one could 
 register for that handle again). This is because I restricted a handle to be registered
 by only 1 user at a time (because of security issue). I could fix this, but I'm too lazy 
 to fix it hehe. I will only use this bot in my personal server (which has like 2 or 3 people anyway)
 - It's currently relying on API calls to Codeforces, which is restricted at 1 call for every 2 seconds. I need 1 API call to load all problems, and 1 API call for each handle to load all submissions. I cached all problems, and only reset it for every 30 minutes, so we could discard the first API call. But it still mean 6 seconds if you have 3 handles, and 8 seconds if you are unlucky and my bot need to fetch new problem. Added a few seconds of processing, and my bot is painfully slow. But yeah, I don't care, I'm too lazy to implement everything

//Basic features

/hello (name): The bot will say "Hello (name)"

/add_handle (handle): Connect that handle to your username. The bot will ask you to do something, and after you are done, use /verify_handle to complete
/verify_handle: Look above
/show_handle_list: show all handles that are associated to you

/train_getproblem (min_rating) (max_rating) (hide_rating) (minimum_id): random a problem rated in [min_rating, max_rating]. The rating won't be shown to you if hide_rating = True. minimum_id is for you if you want to random newer problems only (minimum_id = 1500 mean problems like 1499A will be discarded)

/train_giveup: give up your current problem
/train_complete: After you got Accepted, use this, it will verify for you
/current_problem: Get the problem that you are currently solving