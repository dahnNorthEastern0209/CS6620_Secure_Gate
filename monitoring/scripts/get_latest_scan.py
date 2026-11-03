import sys, boto3

s3 = boto3.client("s3")

def latest(bucket, owner, repo, sha):
    prefix = f"repos/{owner}/{repo}/commits/{sha}/scans/"
    objs = s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])
    if not objs:
        return None
    return max(objs, key=lambda o: o["LastModified"])["Key"]

if __name__ == "__main__":
    print(latest(*sys.argv[1:5]))
