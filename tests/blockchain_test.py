from server_backend.blockchain.blockchain import Blockchain
from server_backend.crypto import ledger_crypto

blockchain = Blockchain()

# Add a signed block
last_hash = blockchain.last_hash()
header = ledger_crypto.create_block_header(index=1, vote_hash="votehash1", previous_hash=last_hash)
signature = ledger_crypto.sign_block_header(header)
blockchain.add_block(vote_hash="votehash1", header_signature=signature)

# Verify
for block in blockchain.to_list_of_dicts():
    print(block)
