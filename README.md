Tribler gossip learning integration
==========

This repository is the result of my Computer Science master's thesis [Distributed Machine Learning Using the Tribler Platform](http://csko.hu/projektek/msc_thesis.pdf). It implements the [Gossip Learning Framework](https://github.com/RobertOrmandi/Gossip-Learning-Framework) as part of a community in Dispersy.

Requirements
===
 - **python2**
 - **python2-mcrypto**
 - **wxpython**
 - **libvlc python binding**
 - bash and standard unix tools
 - gnuplot (optional, for plotting the results)

Experiments
=====

For a detailed description, please see my [thesis](http://csko.hu/projektek/msc_thesis.pdf).
Long story short, you can start a basic experiment by issuing the

``./startExperiment.sh 90``

command, which will start 90 peers to learn on the Iris-setosa-versicolor database using the *P2Pegasos-MU* model, which should converge in a matter of minutes. Beware, this spawns about 2*90 processes and can be quite resource intensive. If you start less peers than there are training examples, the training examples will be distributed as evenly as possible (each peer taking turn in selecting a training example). To switch to the Spambase database, edit `script.py`.

**Don't forget to kill the tribler python processes when you are done.**

Logs
====

Tribler standard output and error channels are redirected to logfiles, which can be found under `logs/`, file names are prefixed with the peer ID. To enable verbose logging, change the logging policy in `dprint.conf`.

The prediction values are logged under `experiment/logs`, file names are prefixed with the peer ID and they also contain the name of the database. These logs are the prediction results at each peer measured every 10 seconds.  Each line has a space-separated columns: UNIX timestamp, peer id, model age, 0-1 error, incoming message count. The last set of columns are the linear model parameters.

Plots
=====

You can aggregate the results even while the experiment is running with the `result.py` script. To create a plot
similar to those in the thesis, save the aggregated results by a command similar to:

`./result.py > experiment/result-p2pegasos-iris-setosa-versicolor.txt`

Then, create a PNG plot using the following command:

`./plot.sh experiment/result-p2pegasos-iris-setosa-versicolor.txt experiment/result-p2pegasos-iris-setosa-versicolor.png`

