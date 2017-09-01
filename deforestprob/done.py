from google.cloud import storage

client = storage.Client()
bucket = client.get_bucket("deforestprob")
blob = bucket.blob("input")
blob.upload_from_string('this is test content!')
