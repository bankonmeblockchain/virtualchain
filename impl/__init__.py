# required callbacks
from reference import get_virtual_chain_name, get_first_block_id, get_magic_bytes, get_opcodes, get_db_state, db_parse, db_check, db_commit, db_save, db_iterable

# optional
try:
   from reference import get_op_processing_order
except:
   def get_op_processing_order():
      return None