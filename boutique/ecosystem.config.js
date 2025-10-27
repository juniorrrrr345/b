module.exports = {
  apps: [{
    name: 'boutique',
    script: 'app.py',
    interpreter: 'python3',
    cwd: '/opt/boutique',
    env: {
      FLASK_ENV: 'production',
      FLASK_DEBUG: 'False',
      SECRET_KEY: 'votre-cle-secrete-tres-longue-et-complexe',
      DATABASE_URL: 'sqlite:///boutique.db'
    },
    restart_delay: 4000,
    max_restarts: 10,
    min_uptime: '10s',
    log_file: './logs/boutique.log',
    out_file: './logs/boutique-out.log',
    error_file: './logs/boutique-error.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    watch: false,
    ignore_watch: ['node_modules', '*.log', 'venv', '__pycache__'],
    instances: 1,
    exec_mode: 'fork'
  }]
}