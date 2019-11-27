# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.network "forwarded_port", guest: 80, host: 80

  config.vm.provider "virtualbox" do |v|
    v.name = "5genesis-portal"
    v.memory = 2048
  end

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    # Exit on error
    set -e

    # Install required packages
    sudo apt-get -y update
    sudo apt-get -y install python3.7 python3.7-venv python3.7-dev python3-pip
    sudo apt-get -y install supervisor nginx git
    python3.7 -m pip install pip
  SHELL

  # Reload shell in order to be able to use pip3.7

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    # Exit on error
    set -e

    # Install requirements. Please consider using virtualenv when installing on a shared machine.
    cd /vagrant
    pip3.7 install -r requirements.txt --user
    pip3.7 install gunicorn --user

    # Configure supervisor
    sudo cp /vagrant/Vagrant/supervisor.conf /etc/supervisor/conf.d/5gportal.conf
    sudo supervisorctl reload

    # Configure nginx (no ssl, see Vagrant/nginx_ssl.conf for an https configuration example)
    sudo rm /etc/nginx/sites-enabled/default
    sudo cp /vagrant/Vagrant/nginx.conf /etc/nginx/sites-enabled/5gportal
    sudo service nginx reload
  SHELL

  config.vm.post_up_message = <<-MESSAGE
    5Genesis Portal should be accessible at localhost (port 80)
  MESSAGE
end