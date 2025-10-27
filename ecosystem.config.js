module.exports = {
  apps: [{
    name: 'telegram-bot',
    script: 'telegram_bot.py',
    interpreter: 'python3',
    cwd: '/opt/telegram-bot',
    env: {
      TELEGRAM_TOKEN: 'TON_TOKEN_ICI',
      ADMIN_PASSWORD: 'TON_MOT_DE_PASSE_ICI',
      DATA_FILE: 'data.json',
      USERS_FILE: 'users.json'
    },
    restart_delay: 4000,
    max_restarts: 10,
    min_uptime: '10s',
    log_file: './bot.log',
    out_file: './bot-out.log',
    error_file: './bot-error.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    watch: false,
    ignore_watch: ['node_modules', '*.log'],
    instances: 1,
    exec_mode: 'fork'
  }]
}