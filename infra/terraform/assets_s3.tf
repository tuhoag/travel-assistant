# General-purpose public-read bucket for app assets served directly to the
# frontend by URL (starting with hotel images, uploaded under a `hotels/`
# prefix — not a dedicated per-feature bucket, so future asset types can
# reuse it). No CloudFront/signing, matching the rest of this stack's
# "simplest thing that works for a demo" posture: public ALBs, a public
# OpenSearch endpoint gated by IAM only, etc. Only store non-sensitive,
# public-by-design content here.

resource "aws_s3_bucket" "assets" {
  bucket = "travel-assistant-assets-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_policy     = false
  restrict_public_buckets = false
  block_public_acls       = true
  ignore_public_acls      = true
}

data "aws_iam_policy_document" "assets_public_read" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.assets.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "assets" {
  bucket     = aws_s3_bucket.assets.id
  policy     = data.aws_iam_policy_document.assets_public_read.json
  depends_on = [aws_s3_bucket_public_access_block.assets]
}

# Browsers load these directly from S3 from the frontend's own origin —
# needs CORS since it's a cross-origin GET.
resource "aws_s3_bucket_cors_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id

  cors_rule {
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
    allowed_headers = ["*"]
  }
}
