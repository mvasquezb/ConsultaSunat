from crontab import CronTab

cron = CronTab()

job = cron.new(command = 'echo ')

job.minute.every(5)




