from time import sleep
import pexpect
import os
from datetime import datetime
import shutil

child = pexpect.spawn('docker attach waage_bds_1 --sig-proxy=false')

def check_active():
    child.sendline('list')
    child.expect('There are ([0-9]+)/([0-9]+) players online:')
    active = int(child.match.group(1).decode('utf8'))
    total = int(child.match.group(2).decode('utf8'))
    return active, total

def do_save():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    tmp_dir = os.path.join('/tmp', timestamp)
    os.mkdir(tmp_dir)
    os.mkdir(os.path.join(tmp_dir, 'db'))

    print('Initiating save')
    child.sendline('save hold')
    i = child.expect(['Saving...\r\n', 'The command is already running\r\n'])

    while True:
        child.sendline('save query')
        i = child.expect(['Data saved. Files are now ready to be copied.\r\n', '\r\n'])
        if i == 0:
            break
        else:
            print('Save files not ready... will retry')
            sleep(1)

    child.expect('\r\n')
    print('Files prepared')
    file_pointers = child.before.decode('utf8').split(', ')

    tmp_files = []
    for file_pointer in file_pointers:
        path, num_bytes = file_pointer.split(':')
        world = os.path.dirname(path)
        name = os.path.basename(path)
        num_bytes = int(num_bytes)
        if (name == 'level.dat' or name == 'level.dat_old' or name == 'levelname.txt'):
            source = os.path.join('/data/worlds/', world, name)
            dest = os.path.join(tmp_dir, name)
        else:
            source = os.path.join('/data/worlds/', world, 'db', name)
            dest = os.path.join(tmp_dir, 'db', name)
        # print(f'Copying {source} -> {dest} ({num_bytes})')
        shutil.copy(source, dest)

        if os.path.getsize(dest) > num_bytes:
            print(f'Truncating {dest} to {num_bytes}')
            f = open(dest, 'w')
            f.truncate(num_bytes)
            f.close()

        tmp_files.append(dest)

    child.sendline('save resume')
    child.expect('Changes to the level are resumed.\r\n')

    archive = os.path.join('/backups', timestamp)
    print(f'Creating archive {archive}')
    shutil.make_archive(archive, 'zip', tmp_dir)
    shutil.rmtree(tmp_dir)
    print(f'Backup {timestamp} complete')

is_active = False
while True:
    active, total = check_active()
    if active > 0:
        is_active = True
        print(f'Players active: {active}/{total}. Triggering backup')
        do_save()
    elif is_active:
        is_active = False
        print('Server transitioned to inactive. Triggering backup')
        do_save()
    else:
        print('Server is idle')
    sleep(900)
