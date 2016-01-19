import os

from config_parameters import all_config_parameters
from time import strftime

testing_dir = "workflows"
batch_template_conf_file = "batch_template.conf"
streaming_template_conf_file = "streaming_template.conf"

default_args = {
  "minInlierRatio": 1.0,
  "minSupport": 0.001,

  "usePercentile": "true",
  "targetPercentile": 0.99,
  "useZScore": "false",
  "zScore": 3.0,

  "inputReservoirSize": 10000,
  "scoreReservoirSize": 10000,
  "inlierItemSummarySize": 1000,
  "outlierItemSummarySize": 10000,
  "summaryRefreshPeriod": 100000,
  "modelRefreshPeriod": 10000,

  "useRealTimePeriod": "false",
  "useTupleCountPeriod": "true",

  "warmupCount": 1000,
  "decayRate": 0.01,

  "alphaMCD": 0.5,
  "stoppingDeltaMCD": 0.001
}

sweeping_parameters = {
  "alphaMCD": [1.0, .95, .75, .5, .25, .1, .05, .01, .001],
  "stoppingDeltaMCD": [1.0, 0.1, 0.01, 0.001, 0.0001],
  "inputReservoirSize": [1, 5, 10, 100, 500, 1000, 4000, 10000, 100000],
  "scoreReservoirSize": [1, 5, 10, 100, 500, 1000, 4000, 10000, 100000],
  "summaryRefreshPeriod": [10, 100, 1000, 10000, 100000, 1, 5],
  "modelRefreshPeriod": [10, 100, 1000, 10000, 100000, 1, 5],

  "minSupport": [1.0, 0.1, 0.01, 0.001, 0.5, 0.8, 0.05],
  "minInlierRatio": [1.0, 0.1, 0.01, 0.001, 0.5, 0.8, 2.0, 5.0, 10.0, 50.0],
  "targetPercentile": [0.9, 0.99, 0.999, 0.5, 0.1, 0.01],

  "warmupCount": [1, 5, 10, 50, 100, 500, 1000, 10000, 100000]
}

def process_config_parameters(config_parameters):
  for config_parameter_type in config_parameters:
    if type(config_parameters[config_parameter_type]) == list:
      config_parameters[config_parameter_type] = ", ".join([str(para) for para in config_parameters[config_parameter_type]])

def create_config_file(config_parameters, conf_file):
  template_conf_file = batch_template_conf_file if config_parameters["isBatchJob"] else streaming_template_conf_file
  template_conf_contents = open(template_conf_file, 'r').read()
  conf_contents = template_conf_contents % config_parameters
  with open(conf_file, 'w') as f:
    f.write(conf_contents)

def parse_results(results_file):
  times = dict()
  num_itemsets = 0
  num_iterations = 0
  with open(results_file, 'r') as f:
    lines = f.read().split('\n')
    for line in lines:
      if line.startswith("DEBUG"):
        if "time" in line:
          line = line.split("...ended")[1].strip()
          line_tokens = line.split("(")
          time_type = line_tokens[0].strip()
          time = int(line_tokens[1][6:-4])
          times[time_type] = time
        elif "itemsets" in line:
          line = line.split("Number of itemsets:")[1].strip()
          num_itemsets = int(line)
        elif "iterations" in line:
          line = line.split("Number of iterations in MCD step:")[1].strip()
          num_iterations = int(line)
  return times, num_itemsets, num_iterations

def run_all_workloads(sweeping_parameter_name=None, sweeping_parameter_value=None):
  if sweeping_parameter_name is not None:
    print "Running all workloads with", sweeping_parameter_name, "=", sweeping_parameter_value
  else:
    print "Running all workloads with default parameters"
  print
  for config_parameters_raw in all_config_parameters:
    config_parameters = {}
    for key in default_args:
      config_parameters[key] = default_args[key]
    for key in config_parameters_raw:
      config_parameters[key] = config_parameters_raw[key]
    if sweeping_parameter_name is not None:
      config_parameters[sweeping_parameter_name] = sweeping_parameter_value
    sub_dir = os.path.join(os.getcwd(), testing_dir, config_parameters["taskName"], strftime("%m-%d-%H:%M:%S"))
    os.system("mkdir -p %s" % sub_dir)
    process_config_parameters(config_parameters)
    conf_file = "batch.conf" if config_parameters["isBatchJob"] else "streaming.conf"
    conf_file = os.path.join(sub_dir, conf_file)
    results_file = os.path.join(sub_dir, "results.txt")
    create_config_file(config_parameters, conf_file)
    cmd = "batch" if config_parameters["isBatchJob"] else "streaming"
    os.system("cd ..; java ${JAVA_OPTS} -cp \"src/main/resources/:target/classes:target/lib/*:target/dependency/*\" macrobase.MacroBase %s %s > %s" % (cmd, conf_file, results_file))
    times, num_itemsets, num_iterations = parse_results(results_file)
    print config_parameters["taskName"], "-->"
    print "Times:", times, ", Number of itemsets:", num_itemsets, ", Number of iterations:", num_iterations
  print

if __name__ == '__main__':
  run_all_workloads()
  for sweeping_parameter_name in sweeping_parameters:
    for sweeping_parameter_value in sweeping_parameters[sweeping_parameter_name]:
      run_all_workloads(sweeping_parameter_name, sweeping_parameter_value)
