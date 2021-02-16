import os
import shutil
import subprocess

import world


async def stop(w):
    w.db.close()
    await w.bot.close()


async def reload(w):
    # fast and dirty. Crash-only is the way to go!
    os.execv(w.entrypoint, sys.argv)


async def snapshot(w):
    backup_path = os.path.join(
        w.datapath,
        "backups",
        datetime.now(timezone.utc).strftime("backup-%Y-%m-%d-%H-%M.sqlite3"),
    )
    w.db.execute("VACUUM INTO ?", (backup_path,))


async def restore(w, backup):
    dbpath = os.path.join(w.datapath, "database.sqlite3")
    backupdbpath = os.path.join(w.datapath, "backups", backup)
    if not os.path.isfile(backupdbpath):
        return
    bw = World()
    bw.db = sqlite3.connect(backupdbpath)
    if not (commit := getSetting(bw, "commit")):
        return
    bw.db.close()
    subprocess.run(["git", "checkout", "-B", "master", commit], check=True)
    w.db.close()
    shutil.copyfile(backupdbpath, dbpath)
    reload()


async def pull(w, repository, refspec):
    snapshot()
    subprocess.run(["git", "pull", "--no-edit", repository, refspec], check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, stdout=PIPE
    ).stdout
    world.updateSetting(w, "commit", commit)
    reload()
