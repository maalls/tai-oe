on prod:

npm run build
sudo systemctl restart rag-frontend


# On prod with nginx

npm run build
sudo cp -r /home/ai/tai-oe/front/dist/* /var/www/gme.ai-oe.co/
sudo chown -R www-data:www-data /var/www/gme.ai-oe.co
sudo chmod -R 755 /var/www/gme.ai-oe.co