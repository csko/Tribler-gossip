set PYTHONPATH=..\..

python test_rquery_reply_active.py singtest_good_simple_reply
python test_rquery_reply_active.py singtest_good_simpleplustorrents_reply
python test_rquery_reply_active.py singtest_bad_not_bdecodable
python test_rquery_reply_active.py singtest_bad_not_bdecodable_torrentfile
