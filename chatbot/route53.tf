# Define an IAM Policy that grants permission to update Route 53 records
resource "aws_iam_policy" "route53_ddns_policy" {
  name        = "NexusAI-Route53-DDNS-Policy"
  description = "Allows EC2 instance to update a specific Route 53 A record"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "route53:ChangeResourceRecordSets"
        ],
        Resource = [
          # CRITICAL: Replace 'YOUR_HOSTED_ZONE_ID' with the actual ID (e.g., Z0123456ABCDEF)
          # This limits the update permission to ONLY this Hosted Zone.
          "arn:aws:route53:::hostedzone/${secrets.ROUTE53_ZONE_ID}"
        ]
      }
    ]
  })
}

# Attach the new policy to the existing EC2 role defined in iam.tf
# The existing role is "aws_iam_role.nexusai_ec2_role".
resource "aws_iam_role_policy_attachment" "route53_ddns_attach" {
  role       = aws_iam_role.nexusai_ec2_role.name
  policy_arn = aws_iam_policy.route53_ddns_policy.arn
}

# Add a variable to pass the Hosted Zone ID securely
variable "ROUTE53_ZONE_ID" {
  description = "The ID of the Hosted Zone where the A record will be updated (e.g., Z123456789)"
  type        = string
}

# NOTE: The Terraform Apply step in your pipeline handles provisioning these new permissions.