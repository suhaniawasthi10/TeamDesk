# TeamDesk infrastructure

Terraform creates the AWS foundation. Helm installs the application and monitoring after the cluster is available.

## Resources

- A dedicated `10.42.0.0/16` VPC with DNS support.
- Two public subnets for the NAT gateway and application load balancer, and two private subnets for EKS workers.
- An internet gateway, route tables, one NAT gateway and its Elastic IP.
- An EKS 1.35 control plane, currently in standard support, with API, audit and authentication logs retained for one day.
- One managed node group with two on-demand `c7i-flex.large` workers: 4 vCPUs and 8 GiB memory total. Each has an encrypted 20 GiB gp3 root disk, no SSH key, and requires IMDSv2. These instance types were returned as Free plan eligible by the EC2 API; `t3.medium` was rejected during the first worker launch.
- Separate cluster and worker IAM roles, plus an EKS administrator access entry for the operator's stable IAM role.
- The Pod Identity agent and EBS CSI driver, pinned to versions compatible with EKS 1.35. Separate IAM roles are associated with the storage and load-balancer controller service accounts in `kube-system`.

Workers have no public IPs. Their image downloads leave through NAT. One NAT gateway is a deliberate short-lived capstone cost tradeoff: it is a single point of failure and traffic from the other availability zone can incur cross-zone transfer charges. Production deployments would usually use one NAT per availability zone.

The Kubernetes API is reachable publicly for local administration and GitHub-hosted runners; it still requires AWS authentication and an EKS access policy. Set `api_allowed_cidrs` to trusted networks when using fixed deployment runners. Application ports are exposed later through an Ingress load balancer, not through the control-plane API.

The AWS provider is pinned and its dependency lockfile is committed. State stays local for this single-operator capstone; do not run Terraform concurrently or delete state before cleanup. A team should use a secured remote backend with locking.

The load-balancer policy in `policies/` comes from the [upstream controller v3.6.0 policy](https://github.com/kubernetes-sigs/aws-load-balancer-controller/blob/v3.6.0/docs/install/iam_policy.json). Terraform additionally restricts security-group ingress edits to this VPC. The storage role uses AWS's `AmazonEBSCSIDriverPolicyV2`. These roles use short-lived Pod Identity credentials; no access keys are stored in Kubernetes. Install the controller and application using the [Helm deployment guide](../helm/teamdesk/README.md).

## Authentication and plan

Requires Terraform 1.10 or newer and AWS CLI v2 supporting `aws login`. Sign in without creating long-lived access keys:

```sh
aws login --profile teamdesk --region ap-southeast-2
export AWS_PROFILE=teamdesk
export AWS_REGION=ap-southeast-2
aws sts get-caller-identity
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

Edit the ignored `terraform/terraform.tfvars` with your account ID and selected region/zones. `allowed_account_ids` prevents using the configuration against a different account. AWS credentials remain in the CLI's credential cache, outside this repository.

If your network cannot resolve the regional STS identity endpoint, `sts_region = "us-east-1"` selects another AWS identity endpoint without moving the infrastructure. This was needed on the development network during planning; omit it when the regional endpoint works.

```sh
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan -out=teamdesk.tfplan
```

Review the plan and estimated charges before applying. Capture the terminal's resource summary for `evidence/M7-plan.png`. Plans, state, credentials and real tfvars are ignored by Git; only the example variables file is committed.

## Estimated credit usage

The following USD list prices were checked on 16 October 2026 for Sydney using the AWS Pricing API, plus the EKS and VPC pricing pages. They describe consumption before eligible credits are applied.

| Resource | Approximate rate |
| --- | ---: |
| EKS in standard support | $0.10/hour |
| Two c7i-flex.large workers | $0.22144/hour combined |
| One NAT gateway | $0.059/hour plus $0.059/GB processed |
| NAT public IPv4 address | $0.005/hour |
| Worker gp3 disks, 40 GiB total | $3.84/month, prorated |
| Later application load balancer | $0.0252/hour plus capacity usage |
| Two load-balancer public IPv4 addresses | $0.01/hour |
| Later PostgreSQL/monitoring gp3 storage | $0.096/GB-month |

The deployed stack's fixed baseline is approximately $0.42–$0.44/hour. For a brief, low-traffic demonstration, allow roughly $0.45–$0.65/hour ($3.60–$5.20 for eight hours), including a small allowance for downloads, logs and load-balancer capacity. This is an estimate, not a spending cap; traffic, storage, runtime and service eligibility affect the bill. The Free plan's displayed $100 balance is not permission to upgrade to a Paid plan. If a service is blocked, review the restriction before changing plans.

Sources: [EKS pricing](https://aws.amazon.com/eks/pricing/), [VPC pricing](https://aws.amazon.com/vpc/pricing/), [EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/), [EBS pricing](https://aws.amazon.com/ebs/pricing/), [load balancer pricing](https://aws.amazon.com/elasticloadbalancing/pricing/).

## Provision and verify

Applying starts billable usage, consuming applicable credits. Use the reviewed saved plan:

```sh
terraform -chdir=terraform apply teamdesk.tfplan
mkdir -p .local
export KUBECONFIG="$PWD/.local/kubeconfig"
aws eks update-kubeconfig --profile teamdesk --region ap-southeast-2 --name teamdesk --alias teamdesk
kubectl get nodes
```

The project-local kubeconfig is ignored and leaves other Kubernetes contexts untouched. If Terraform reports a DNS lookup failure on macOS while system lookups work, retry the command with `GODEBUG=netdns=cgo` to select the system resolver. Regenerate and review a plan if Terraform reports that a saved plan is stale.

Capture the VPC and EKS cluster in the AWS Console with the region visible. This phase must actually finish before it counts as deployed infrastructure. The `terraform output` values identify the resources to capture.

## Cleanup

Keep the cluster until the required demonstration and evidence are complete. Uninstall application/Ingress and monitoring Helm releases first, and wait for their AWS load balancers to be deleted. Remove Kubernetes-created PVCs and confirm their EBS volumes have been deleted when data is no longer needed; Terraform does not own these resources.

Then review and execute destruction:

```sh
terraform -chdir=terraform plan -destroy -out=destroy.tfplan
terraform -chdir=terraform apply destroy.tfplan
```

Capture the successful `Destroy complete!` output as `evidence/M7-destroy.png`. Check for leftover project load balancers, EBS volumes, NAT gateways and Elastic IPs. Keep local state until cleanup is confirmed. Stopping the application or closing the terminal does not stop EKS/NAT charges.

### Verified cleanup

The TeamDesk deployment was removed on 16 October 2026. Application and monitoring removal deleted the ALB, its target groups and the three data volumes before the controllers were removed. Terraform deleted the 37 managed resources. The initial run removed 36 resources but encountered a DNS lookup failure when deleting the CloudWatch log group; a refreshed destroy plan removed that final resource successfully.

The final AWS audit found no remaining TeamDesk EKS cluster, active workers, worker Auto Scaling group, load balancer, target groups, EBS volumes or snapshots, NAT gateway, Elastic IP, VPC, subnets, route tables, network interfaces, security groups, project IAM roles/policy or CloudWatch log group. The five recorded EBS disks included both worker root volumes. Terraform state contains no managed resources. GitHub's deployment variable is disabled and its temporary cluster credential has been removed.
