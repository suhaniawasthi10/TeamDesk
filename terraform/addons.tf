locals {
  controller_accounts = {
    ebs = "ebs-csi-controller-sa"
    alb = "aws-load-balancer-controller"
  }
}

resource "aws_eks_addon" "pod_identity" {
  cluster_name  = aws_eks_cluster.main.name
  addon_name    = "eks-pod-identity-agent"
  addon_version = "v1.4.0-eksbuild.4"
  depends_on    = [aws_eks_node_group.main]
}

resource "aws_iam_role" "controller" {
  for_each = local.controller_accounts
  name     = "${var.project_name}-${each.key}-controller"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "pods.eks.amazonaws.com" }
      Action    = ["sts:AssumeRole", "sts:TagSession"]
      Condition = {
        StringEquals = {
          "aws:RequestTag/kubernetes-namespace"       = "kube-system"
          "aws:RequestTag/kubernetes-service-account" = each.value
          "aws:RequestTag/eks-cluster-name"           = aws_eks_cluster.main.name
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ebs" {
  role       = aws_iam_role.controller["ebs"].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEBSCSIDriverPolicyV2"
}

# Upstream v3.6.0 policy, with security-group ingress edits restricted to this VPC.
resource "aws_iam_policy" "alb" {
  name = "${var.project_name}-load-balancer-controller"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [for statement in jsondecode(file("${path.module}/policies/load-balancer-controller.json")).Statement :
      merge(statement, contains(statement.Action, "ec2:AuthorizeSecurityGroupIngress") ? {
        Condition = merge(try(statement.Condition, {}), {
          ArnEquals = {
            "ec2:Vpc" = aws_vpc.main.arn
          }
        })
      } : {})
    ]
  })
}

resource "aws_iam_role_policy_attachment" "alb" {
  role       = aws_iam_role.controller["alb"].name
  policy_arn = aws_iam_policy.alb.arn
}

resource "aws_eks_pod_identity_association" "controller" {
  for_each        = local.controller_accounts
  cluster_name    = aws_eks_cluster.main.name
  namespace       = "kube-system"
  service_account = each.value
  role_arn        = aws_iam_role.controller[each.key].arn
  depends_on      = [aws_eks_addon.pod_identity, aws_iam_role_policy_attachment.ebs, aws_iam_role_policy_attachment.alb]
}

resource "aws_eks_addon" "ebs" {
  cluster_name  = aws_eks_cluster.main.name
  addon_name    = "aws-ebs-csi-driver"
  addon_version = "v1.67.0-eksbuild.1"
  depends_on    = [aws_eks_pod_identity_association.controller]
}
