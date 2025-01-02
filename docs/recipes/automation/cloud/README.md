# Cloud Automation

The goal of this automation is to create a fully running TIBCO Platform environment in cloud platform such as Amazon Web Services (AWS), Microsoft Azure, and Google Cloud Platform 
from scratch with a single script using a Bastion host on the respective cloud platform.

Each of the respective scripts basically 
* Install required software on the Bastion host
* Prepares required configuration
* Execute headless platform provisioner

To use these scripts, follow the steps below.

> [!NOTE]
> The steps below were tested from a Microsoft Windows 11 workstation. However, it should be easily adaptable to other operating systems of your choice.

> [!NOTE]
> All value within \<\< >> is replacable.

#### Table of Contents

1. [Pre-requisite](#prereq)
2. [Step 1 - Create Bastion host](#step1)
3. [Step 2 - Provision Kubernetes Cluster](#step2)
4. [Step 3 - Register Data Plane](#step3)
5. [Step 4 - Setup Data Plane In Control Plane](#step4)
6. [Tear down](#teardown)
7. [Additional Optional Steps](#optional)
    - [Step - Setup Public Certificate](#pubcert)
8. [References](#ref)

# Steps

<a name="prereq" />

## Pre-requisite - Create the following objects if it does not already exists.

### Local Microsoft Windows Workstation
- Copy all files from this folder to an empty local folder.

### For AWS Only

- Key Pairs > Create key pair
    - Name: \<\<user-kp>>
    - Key pair type: RSA
    - Private key file format: .pem \
      Note: Save the .pem file to C:\Users\\\<\<username>>\\\<\<user-kp.pem>>. You will need this to connect to the EC2.

- Security Groups > Create security group
    - Security group name: \<\<user-sg>> - Description: <<...>>
    - Inbound rules
        - Add rule - Type: SSH - Source: \<\<My IP>>
    - Select *Create security group*

- IAM > Policies > Create policy
    - Specify permissions > JSON

        ```json
        {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "eks:*", "Resource": "*"},
                {"Effect": "Allow", "Action": ["ssm:GetParameter", "ssm:GetParameters"], "Resource": ["arn:aws:ssm:*:<<ACCOUNT>>:parameter/aws/*", "arn:aws:ssm:*::parameter/aws/*"]},
                {"Effect": "Allow", "Action": ["kms:CreateGrant", "kms:DescribeKey"], "Resource": "*"},
                {"Effect": "Allow", "Action": ["logs:PutRetentionPolicy"], "Resource": "*"}
            ]
        }
        ```

    - Policy name: EksAllAccess
    - Select *Create policy*
    
- IAM > Policies > Create policy
    - Specify permissions > JSON

        ```json
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:CreateInstanceProfile", "iam:DeleteInstanceProfile", "iam:GetInstanceProfile", "iam:RemoveRoleFromInstanceProfile", "iam:GetRole", "iam:CreateRole", "iam:DeleteRole",
                        "iam:AttachRolePolicy", "iam:PutRolePolicy", "iam:AddRoleToInstanceProfile", "iam:ListInstanceProfilesForRole", "iam:PassRole", "iam:DetachRolePolicy", "iam:DeleteRolePolicy",
                        "iam:GetRolePolicy", "iam:GetOpenIDConnectProvider", "iam:CreateOpenIDConnectProvider", "iam:DeleteOpenIDConnectProvider", "iam:TagOpenIDConnectProvider", "iam:ListAttachedRolePolicies",
                        "iam:TagRole", "iam:GetPolicy", "iam:CreatePolicy", "iam:DeletePolicy", "iam:ListPolicyVersions"
                    ],
                    "Resource": [
                        "arn:aws:iam::<<ACCOUNT>>:instance-profile/eksctl-*", "arn:aws:iam::<<ACCOUNT>>:role/eksctl-*", "arn:aws:iam::<<ACCOUNT>>:policy/eksctl-*", "arn:aws:iam::<<ACCOUNT>>:oidc-provider/*",
                        "arn:aws:iam::<<ACCOUNT>>:role/aws-service-role/eks-nodegroup.amazonaws.com/AWSServiceRoleForAmazonEKSNodegroup", "arn:aws:iam::<<ACCOUNT>>:role/eksctl-managed-*"
                    ]
                },
                {"Effect": "Allow", "Action": ["iam:GetRole"], "Resource": ["arn:aws:iam::<<ACCOUNT>>:role/*"]},
                {"Effect": "Allow", "Action": ["iam:CreateServiceLinkedRole"], "Resource": "*", "Condition": {"StringEquals": {"iam:AWSServiceName": ["eks.amazonaws.com", "eks-nodegroup.amazonaws.com", "eks-fargate.amazonaws.com"]}}}
            ]
        }
        ```
          
    - Policy name: IamLimitedAccess
    - Select *Create policy*

- IAM > Roles > Create role
    - Trusted entity type: AWS account
    - An AWS account: \<\<This account>>
    - Add permissions
        - AmazonEC2FullAccess - AWS managed
        - AmazonElasticFileSystemFullAccess - AWS managed
        - AWSCloudFormationFullAccess - AWS managed
        - EksAllAccess - Customer managed
        - IamLimitedAccess - Customer managed
    - Role name: platform-provisioner
    -  Select *Create role* \
      Note: The list of permissions are what was tested successfully. There might be opportunities to further reduce the grants.

### For Azure Only

- Resource groups > Create
    - Subscription: <<...>> 
    - Resource group: \<\<user-rg>>
	  Note: This resource group is different than the TP_RESOURCE_GROUP in the config.props below. If not, the teardown will kill the Bastion host as well.
    - Region: <<(US) East US>>
    - Select *Review + create* and then *Create*
    
- SSH keys > Create
    - Subscription: <<...>> 
    - Resource group: \<\<user-rg>>
    - Region: \<\<(US) East US>>
    - Key pair name: \<\<user-kp>>
    - SSH public key source: Generate new key pair
    - SSH Key Type: RSA SSH Format
    - Select *Review + create* and then *Create*
    - Select *Download private key and create resource* \
      Note: Save the .pem file locally in a folder with permission control (recommended at C:\\Users\\\<\<username>>\\\<\<user-kp.pem>>). You will need this to connect to the Bastion host.

- Network security groups > Create
    - Subscription: <<...>>
    - Resource group: \<\<user-rg>> 
    - Name: \<\<user-nsg>>
    - Region: \<\<East US>>
    - Select *Review + create* and then *Create*
    - Go to resource > Settings > Inbound security rules > Add
        - Source: IP Addresses
        - Source IP addresses/CIDR range: \<\<0.0.0.0/32>> 
        - Service: SSH 
        - Action: Allow 
        - Name: \<\<AllowCidrBlockSSHInbound>>
    - Select *Add*

- Virtual networks > Create
    - Subscription: <<...>>
    - Resource group: \<\<user-rg>> 
    - Name: \<\<user-vnet>>
        - Region: \<\<(US) East US>>
    - Select *Review + create* and then *Create* 

### For GCP Only

- Command Prompt: ssh-keygen -t rsa -f C:\Users\\\<\<username>>\\\<\<user-kp.pem>> -C ubuntu
    - Enter passphrase (empty for no passphrase): [Empty]
    - Enter same passphrase again: [Empty] \
      Note: Private key will be <<user-kp.pem>> and public key will be <<user-kp.pem.pub>>

<a name="step1" />

## Step 1 - Create Bastion host

### For AWS Only

- EC2 > Launch instance
    - Name:\<\<tp-bastion>>
    - Application and OS Images > Quick Start > Ubuntu
        - Amazon Machine Images (AMI): Ubuntu Server 24.04 LTS (HVM), SSD Volume Type
    - Instance type: t3a.2xlarge (Note: 8 vCPU, 32 GiB Memory $0.3008 per Hour)
    - Key pair name: \<\<The key pair created previously>>
    - Network settings > Firewall (security groups) > Select existing security group
        - Common security groups: \<\<The security group created previously>>
    - Configure storage: 1x 30 GiB gp3 Root volume (Not encrypted)
    - Select *Launch instance*

### For Azure Only

- Virtual machines > Create > Azure virtual machine
    - Subscription: <<...>>
    - Resource group: \<\<user-rg>>
    - Virtual machine Name: \<\<tp-bastion>> 
    - Region: <<(US) East US>>
    - Image: Ubuntu Server 24.04 LTS - x64 Gen2
    - VM architecture: x64
    - Size: Standard_D8s_v3 (Note: General purpose 8 vCPU, 32 GiB Memory $167.90 = $0.2331 per Hour)
    - Authentication type: SSH public key
    - Username: ubuntu
    - SSH public key source: Use existing key stored in Azure 
    - Stored Keys: \<\<user-kp>>
    - Public inbound ports: None
- Select *Next: Disks* and then *Next: Networking*
    - Virtual network: \<\<user-vnet>> 
    - Public IP: (new) tp-bastion-ip
    - NIC network security group: Advanced 
    - Configure network security group: \<\<user-nsg>>
    - Delete public IP and NIC when VM is deleted: [Checked]
- Select *Review + create* and then *Create*

### For GCP Only

- Compute Engine > VM instances > Create Instance
    - Machine configuration
        - Name: \<\<tp-bastion>>
        - Region: \<\<us-central1 (Iowa)>>
        - Zone: Any
        - Machine configuration: General purpose - E2
        - Machine type: 
            - Preset: e2-standard-8 (8 vCPU, 4 core, 32 GB memory) with 10GB balanced persistent disk $196.67 per Month = 0.2732 per Hour
    - Select *OS and storage > Change*
        - Operating system: Ubuntu
        - Version: Ubuntu 24.04 LTS x86/64,amd64 
        - Boot disk type: Balanced persistent disk - Size (GB): 30
        - Select *Select*
    - Select *Security > Manage Access - Add manually generated SSH keys > + Add Item*
            - \<\<Use file content from user-kp.pem.pub>>
    - Select *Create*

<a name="step2" />

## Step 2 - Provision Kubernetes Cluster

1. From Windows Command Prompt

    ```   
    set UserName=<<ubuntu>>
    set PublicEndpoint=<<AWS: ec2-34-207-144-190.compute-1.amazonaws.com or AWS/Azure/GCP: 52.146.88.196>>
    set KeyPair=<<%userprofile%/user-kp.pem>>
    set ScriptFile=<<Full path with wildcard to local folder where the automation script was copied to in pre-requisite, e.g. C:\MySrc\github\platform-provisioner\docs\recipes\automation\cloud\*>>
    scp -o "StrictHostKeyChecking no" -i "%KeyPair%" "%ScriptFile%" %UserName%@%PublicEndpoint%:/home/%UserName%
    ssh -o "StrictHostKeyChecking no" -o ServerAliveInterval=60 -i "%KeyPair%" %UserName%@%PublicEndpoint%
    chmod +x *.sh
    ```

> [!NOTE]
> IMPORTANT - If you are using TIBCO managed SSO for AWS, use the View role for the proceeding steps. Otherwise, just use your standard AWS credential. 

2. Execute the script with proper credential, selecting Start Type: 1 (Verify Access) and re-executing the script selecting Start Type: 2 (Create)

    ```
    #### For AWS Only ####
    
    # Copy the export lines below from AWS access portal - \<\<AWS account>> - \<\<role>> - Access keys - Option 1: Set AWS environment variables and run it on the Bastion host.
    export AWS_ACCESS_KEY_ID=<<...>>
    export AWS_SECRET_ACCESS_KEY=<<...>>
    export AWS_SESSION_TOKEN=<<...>>
    
    ./setup-dp-eks-platformprovisioner.sh
    
    #### For Azure Only ####
    
    ./setup-dp-aks-platformprovisioner.sh

    ##### For GCP Only ####
    
    ./setup-dp-gke-platformprovisioner.sh
    
    # If you get a ERROR: (gcloud.beta.container.clusters.create) ResponseError: code=400, message=Master version must be one of "REGULAR" channel supported versions...,
    # update the TP_CLUSTER_VERSION in config.props with the list of version supported as given by the error message.
    # Run source setenv.sh, Start Type: 3 (Teardown) and rerun Start Type: 2 (Create)
    ```

> [!NOTE]
> This step will create a blank config.props file if one does not already exists. Update the config file with the desired values and re-execute the scipt.

> [!NOTE] 
> This step might also reboot the Bastion host if it is installing docker for the first time. If it does, just re-execute Step 2.

> [!NOTE] 
> For Azure and GCP, if it is your first time running the script, it will prompt you for credentials once it has sufficient dependencies installed.

3. Verify access to the Kubernetes cluster by executing the below.

    ```
    source ${HOME}/setenv.sh
    kubectl get nodes
    ```

<a name="step3" />

## Step 3 - Register Data Plane

1. Use a browser and login to TIBCO Platform Control Plane (e.g., https://\<\<...>>.tibco.com)

2. Register a Data Plane > Existing Kubernetes Cluster - Start
    - Data Plane Name: \<\<dev-dp-eks>>
    - Provider: AWS
    - Region: \<\<N. Virginia (us-east-1)>>
    - I have read and accepted the TIBCO End User Agreement (EUA): [Checked]
    - Select *Next*
    - Namespace: \<\<tibco-ns>>
    - Service Account: \<\<tibco-sa>>
    - Allow cluster scoped permissions: [Enabled]
    - Select *Next*
    - Deployment of fluentbit sidecar for Services logs: [Checked]
    - Select *Next*
    - Capture the commands below to be run from the Bastion host (remember to run "source ${HOME}/setenv.sh" first if you have not done so already). \
      Note: The below is just a sample. Do not run as-is. 

        ```
        === Namespace Creation ===
        kubectl apply -f - <<EOF
        apiVersion: v1
        kind: Namespace
        metadata:
          name: tibco-ns
          labels:
            platform.tibco.com/dataplane-id: csuhcc6h8mo4uiepu5b0
        EOF

        === Service Account Creation ===
        helm upgrade --install -n tibco-ns dp-configure-namespace dp-configure-namespace --repo https://tibcosoftware.github.io/tp-helm-charts --version 1.3.4 --set global.tibco.dataPlaneId=<<...>> --set global.tibco.primaryNamespaceName=tibco-ns --set global.tibco.serviceAccount=tibco-sa --set global.tibco.enableClusterScopedPerm=true

        === Cluster Registration ===
        helm upgrade --install dp-core-infrastructure dp-core-infrastructure -n tibco-ns --repo https://tibcosoftware.github.io/tp-helm-charts --version 1.3.16 --set global.tibco.dataPlaneId=<<...>> --set global.tibco.subscriptionId=cn1r99d8el1deih7pkt0 --set tp-tibtunnel.configure.accessKey=<<...>> --set tp-tibtunnel.connect.url=<<...>> --set global.tibco.containerRegistry.url=csgprduswrepoedge.jfrog.io --set global.tibco.serviceAccount=tibco-sa --set global.tibco.containerRegistry.username=<<...>> --set global.tibco.containerRegistry.password=<<...>> --set global.tibco.containerRegistry.repository=tibco-platform-docker-prod --set global.tibco.containerRegistry.email=tibco-plt@cloud.com --set global.proxy.noProxy='' --set global.logging.fluentbit.enabled=true
        ```

    - Select *Done*

<a name="step4" />

## Step 4 - Setup Data Plane In Control Plane

### Configure Storage Class and Ingress Controller

1. Go to Data Plane > Data Plane configuration > Add Storage Class
    - Resource Name: diskstorageclass
    - Description: disk storage class
    - Storage Class Name: ebs-gp3
    - Select *Add*

2. Go to Data Plane > Data Plane configuration > Add Ingress Controller
    - Ingress Controller: nginx
    - Resource Name: bwce
    - Ingress Class Name: nginx
    - FQDN: bwce.tp-ingress.cs-nam.dataplanes.pro
    - Select *Add*

3. Go to Data Plane > Data Plane configuration > Add Ingress Controller
    - Ingress Controller: nginx
    - Resource Name: flogo
    - Ingress Class Name: nginx
    - FQDN: flogo.tp-ingress.cs-nam.dataplanes.pro
    - Select *Add*

### Configure Observability 

1. Go to Data Plane > Data Plane configuration > Observability > Add new resource
2. Configure Log Server
    - Data plane resource name: user-app-log
    - User Apps
        - Query Service enabled: [Enabled]
        - Query Service configurations > Add Query Service Configuration 
            - Query Service name: user-app-query-service
            - Query Service type: ElasticSearch
            - Log Index: user-app-dp 
            - Endpoint: https://dp-config-es-es-http.elastic-system.svc.cluster.local:9200
            - Username: elastic
            - Password: \<\<...>> (Use kubectl get secret dp-config-es-es-elastic-user -n elastic-system -o jsonpath="{.data.elastic}" | base64 --decode; echo)
            - Select *Save Query Service*
        - Exporter enabled: [Enabled]
        - Exporter configurations > Add Exporter configuration
            - Exporter name: user-app-exporter
            - Exporter type: ElasticSearch
            - Log Index: user-app-dp 
            - Endpoint: https://dp-config-es-es-http.elastic-system.svc.cluster.local:9200
            - Username: elastic
            - Password: \<\<...>> (Use kubectl get secret dp-config-es-es-elastic-user -n elastic-system -o jsonpath="{.data.elastic}" | base64 --decode; echo)        
            - Select *Save Exporter*
        - Services
        - Exporter enabled: [Enabled]
        - Exporter configurations > Add Exporter Configuration
            - Exporter name: service-exporter
            - Exporter type: ElasticSearch
            - Log Index: tibco-services-dp 
            - Endpoint: https://dp-config-es-es-http.elastic-system.svc.cluster.local:9200
            - Username: elastic
            - Password: \<\<...>> (Use kubectl get secret dp-config-es-es-elastic-user -n elastic-system -o jsonpath="{.data.elastic}" | base64 --decode; echo)        
            - Select *Save Exporter*
        - [Select All] > Next 

3. Configure Metrics Server
    - Query Service configurations > Add Query Service Configuration 
        - Query Service name: metrics-query-service
        - Query Service type: Prometheus
        - Endpoint: http://kube-prometheus-stack-prometheus.prometheus-system.svc.cluster.local:9090
        - Username: 
        - Password: 
        - Select *Save Query Service*
    - Exporter enabled: [Enabled]
    - Exporter configurations > Add Exporter configuration
        - Exporter name: metrics-exporter
        - Exporter type: Prometheus
        - Select *Save Exporter*
    - [Select All] > Next

4. Configure Traces Server
    - Query Service enabled: [Enabled]
    - Query Service configurations > Add Query Service Configuration 
        - Query Service name: traces-query-service
        - Query Service type: ElasticSearch
        - Endpoint: https://dp-config-es-es-http.elastic-system.svc.cluster.local:9200
        - Username: elastic
        - Password: \<\<...>> (Use kubectl get secret dp-config-es-es-elastic-user -n elastic-system -o jsonpath="{.data.elastic}" | base64 --decode; echo)
        - Select *Save Query Service*
    - Exporter enabled: [Enabled]
    - Exporter configurations > Add Exporter configuration
        - Exporter name: traces-exporter
        - Exporter type: ElasticSearch
        - Endpoint: https://dp-config-es-es-http.elastic-system.svc.cluster.local:9200
        - Username: elastic
        - Password: \<\<...>> (Use kubectl get secret dp-config-es-es-elastic-user -n elastic-system -o jsonpath="{.data.elastic}" | base64 --decode; echo)        
        - Select *Save Exporter*
    - [Select All] > Save
  
### Provision Capabilities

> [!NOTE]
> After provisioning each capabilities below, you might have to wait a little while for it to detect the status and turn green.

#### Provision BWCE

1. Go to Data Plane > Provision a capability > Provision TIBCO BusinessWorks Container Edition > Start
    - Storage Class (1): diskstorageclass
    - Ingress Controller (2): bwce
2. Select *Next* 
    - Path Prefix (leave this as-is, else provisioning will fail): /tibco/bw/\<\<...>>
    - I have read and accepted the TIBCO End User Agreement (EUA): [Checked]
3. Select *BWCE Provision Capability*

#### Provision Flogo

1. Go to Data Plane > Provision a capability > Provision TIBCO Flogo Enterprise > Start
    - Storage Class (1)
    - Ingress Controller (2): flogo
2. Select *Next*
    - Path Prefix (leave this as-is): /tibco/flogo/\<\<...>>
    - I have read and accepted the TIBCO End User Agreement (EUA): [Checked]
3. Select *Provision Flogo Version*

#### Provision EMS

1. Go to Data Plane > Provision a capability > Provision TIBCO Enterprise Message Service > Start
    - Message Storage 1: diskstorageclass
    - Log Storage 1: diskstorageclass
2. Select *Next*
    - Server Name: \<\<ems1>>
    - Server Environment: \<\<dev>>
    - Server Sizing: \<\<small>>
    - Capability is for production: [Unchecked]
    - Logs storage is shared: [Unchecked]
    - Use Custom Config: [Unchecked]
    - I have read and accepted the TIBCO End User Agreement (EUA): [Checked]
3. Select *Next*
4. Select *Provision TIBCO Enterprise Message Service*

#### Provision Service Mesh

1. Go to Data Plane > Provision a capability > Provision Service Mesh > Start
    - I have read and accepted the TIBCO End User Agreement (EUA): [Checked]
2. Select *Provision capability*

#### Provision Quasar

1. Go to Data Plane > Provision a capability > Provision TIBCO Messaging Quasar - Powered by Apache Pulsar > Start
    - Message Storage: diskstorageclass
    - Journal Storage: diskstorageclass
    - Log Storage: diskstorageclass
2. Select *Next*
    - Server Name: \<\<pulsar1>>
    - Server Environment: \<\<dev>>
    - Server Sizing: \<\<small>>
    - Capability is for production: [Unchecked]
    - Logs storage is shared: [Unchecked]
    - Use Custom Config: [Unchecked]
    - I have read and accepted the TIBCO End User Agreement (EUA): [Checked]
3. Selext *Next*
3. Select *Provision TIBCO Messaging Quasar - Powered by Apache Pulsar*

#### Provision Developer Hub

1. Go to Data Plane > Provision a capability > Provision TIBCO Developer Hub > Start
...

<a name="teardown" />

## Tear down

1. Control plane (e.g., https://\<\<...>>.tibco.com): De-provision all capabilities

    - Control plane > \<\<dp-eks>> > ... > Delete Data Plane (or Force Delete Data Plane, if the first method does not work)
    - Capture the commands below to be run from the EC2 Bastion below (remember to "source ${HOME}/setenv.sh" before you run the command). Sample below but do not use the sample.

        ```
        helm uninstall -n tibco-ns dp-core-infrastructure 
        helm uninstall -n tibco-ns dp-configure-namespace
        kubectl delete ns tibco-ns
        ```

    - I confirm that this data plane can be deleted and I have either copied or downloaded the commands for manual cleanup.: [Checked]
    - Select *Delete*

> [!NOTE]
> If you get an error deleting, you can use Force Delete Data Plane

2. EC2 Bastion: Run ./setup-dp-eks-platformprovisioner.sh
    - Start Type: 3 (Teardown)

### For AWS Only

> [!NOTE]
> If you get an error "...not able to delete stack...not authorized to perform: cloudformation:DeleteStack...", you can try the alternate method below.

    ```
    source ${HOME}/setenv.sh
    eksctl delete cluster --name="${TP_CLUSTER_NAME}" --disable-nodegroup-eviction --force --profile main-${ACCOUNT}-assumerole
    ```

Even though the script completed successfully, the CloudFormation stack might still be deleting. Check CloudFormation 

> [!NOTE]
> If you are using TIBCO managed SSO for AWS, use the Use role. 

You should only have one stack there eksctl-<<...>>-tp-eks-cluster-cluster with DELETE_IN_PROGRESS status. 
If the status goes into DELETE_FAILED, select the stack and click "Retry delete". Then select "Force delete this entire stack" and click "Delete". Wait for the stack to be completely deleted and removed.

3. Cleanup any remaining remnants such as EFS, ELB, and VPC not cleaned up from CloudFormation. 

    - EC2 Bastion: Run ./setup-dp-eks-platformprovisioner.sh
        - Start Type: 4 (Cleanup)

<a name="optional" />

### For Azure Only

No additional steps needed for Azure.

### For AWS Only

No additional steps needed for GCP.

## Additional Optional Steps

<a name="pubcert" />

### Step - Setup Public Certificate - this step is optional and only if you need tls access to applications in the platform

- Go to Certificate Manager > Request certificate > Request a public certificate > Next
    - Fully qualified domain name: *.\<\<tp-ingress.cs-nam.dataplanes.pro>>
    - Select *Request*
    - Create records in Route 53 > Create records
    - [Wait a few minutes] > View certificate 
    - Note: The status of the domain should turn into Success.

    - Validation:
        - Using Windows command prompt or Linux terminal
        
            ```
            nslookup <<bwce.tp-eks-ingress.cs-nam.dataplanes.pro>>
            
            Output: (similar to below) 
            Server:  MUEPCLOUDDC01.corp.cloud.com
            Address:  10.164.2.10

            Non-authoritative answer:
            Name:    bwce.tp-eks-ingress.cs-nam.dataplanes.pro
            Address:  3.226.108.156
            ```
<a name="ref" />

## References
- Workshop: https://github.com/TIBCOSoftware/tp-helm-charts/tree/main/docs/workshop/eks/data-plane
- Platform Provisioner: https://github.com/TIBCOSoftware/platform-provisioner