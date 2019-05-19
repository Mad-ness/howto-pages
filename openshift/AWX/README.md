# Creating and Using Templates

In this work you need to create a template and run **AWX** application from this. This application is a main stream project for **Red Hat Ansible Tower**. It consists of a few microservices and fits very good for this lab.


## YAML Files

There are given a number of YAML files from which you need to create a template. These files can be run separately and used independently but some of them depends on the other ones.

This directory also contains a final template `awx-template.yaml`. Try to not use this and create your own one.

### List of YAML files

- `configmap.rabbitmq-config.yaml` - configuration files for **RabbitMQ**
- `configmap.awx-config.yaml` - configuration files for **AWX**
- `secret.awx-secrets.yaml` - configuration files and some variables with *secret* data
- `deploymentconfig.postgresql.yaml` - deployment config and a service for a *PostgreSQL* database
- `statefulset.awx-rabbitmq.yaml` - statefulset and a service for *RabbitMQ* messaging bus
- `statefulset.awx-task.yaml` - includes a service account `awx`, a statefulset, and a service for running *AWX-Task* service
- `statefulset.awx-web.yaml` defines a statefulset, a service, and a route for *AWX Web* service
- `statefulset.awx-memcached.yaml` includes a statefulset and a service for *MemCached* service



### Dependencies


The config maps and the secret should be created first because they are used by RabbitMQ, PostgreSQL. Services 
*RabbitMQ*, *MemCached*, and *PostgreSQL* might be created afterwards. 
Then, AWX-Task and AWX-Web. Initialization of AWX-Task takes some time since it populates the database records.


### Special Actions

AWX-Task requires advanced permissions. This is why there is a creating of `awx` service account. 
You need to have cluster-admin privileges to give this account needed permissions. Once you are ready do this:

    oc adm policy add-scc-to-user privileged -z awx -n <project>


## Creating the Objects

Create the needed instances in the mentioned order and make sure everything is running successfully.


## What to Improve

* Passwords, logins, hostnames for RabbitMQ, PostgreSQL, and MemCached mentioned in a few places. Ideally it should be mentioned only one time.
* Scalability have not been tested and it should not work out of box.
* Username and Password for AWX's admin user is hardcoded
* PostgreSQL database does not have a permanent storage
* Limits cannot be adjusted without modifying the resources in the template
* Versions of images are hardcoded in the template


## Authors

* Dmitrii Mostovshchikov <dmadm2008@gmail.com>


