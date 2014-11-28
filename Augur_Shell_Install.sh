#!/bin/bash
killall python
killall Python
rm -rf augur
git clone https://github.com/AugurProject/augur.git
cd augur
pip install -r requirements.txt
echo "Augur started, go to http://127.0.0.1:9000/ in your web browser"
./augur_ctl start