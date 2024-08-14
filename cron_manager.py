from crontab import CronTab

cron = CronTab(user=True)
test_job = cron.new(command='echo "hello"', comment='crossref')
test_job.month.every(1)
#cron.write()
for job in cron:
    print(job)

cron.remove(test_job)