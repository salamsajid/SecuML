## SecuML
## Copyright (C) 2016-2017  ANSSI
##
## SecuML is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## SecuML is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with SecuML. If not, see <http://www.gnu.org/licenses/>.

import matplotlib.pyplot as plt
import pandas as pd

from SecuML.Plots.PlotDataset import PlotDataset
from SecuML.Tools import dir_tools

class TrainTestValidationPerformanceMonitoring(object):

    def __init__(self, monitoring, model_name, train_test_validation):
        self.monitoring = monitoring
        self.model_name = model_name
        self.train_test_validation = train_test_validation
        self.setIsMulticlassModel()
        self.setPerfIndicators()

    def setIsMulticlassModel(self):
        train_test = self.monitoring.iteration.update_model
        model_conf = train_test.models[self.model_name].conf
        self.multiclass = model_conf.families_supervision

    def getEvolutionFile(self, evolution_dir):
        evolution_file  = evolution_dir
        evolution_file += self.model_name + '_'
        evolution_file += self.train_test_validation
        evolution_file += '_monitoring.csv'
        return evolution_file

    def setPerfIndicators(self):
        model = self.monitoring.iteration.update_model.models[self.model_name]
        if self.train_test_validation == 'train':
            monitoring = model.training_monitoring
        elif self.train_test_validation == 'cv':
            monitoring = model.cv_monitoring
        elif self.train_test_validation == 'test':
            monitoring = model.testing_monitoring
        elif self.train_test_validation == 'validation':
            monitoring = model.validation_monitoring
        else:
            raise ValueError('Invalid value for train_test_validation, got %s' % self.train_test_validation)
        self.perf_indicators = monitoring.performance_monitoring.perf_indicators

    def generateMonitoring(self):
        return

    def exportMonitoring(self, monitoring_dir, evolution_dir):
        evolution_file = self.getEvolutionFile(evolution_dir)
        self.displayCsvLine(evolution_file)
        self.plotEvolutionMonitoring(evolution_file, monitoring_dir)

    def displayCsvLine(self, evolution_file):
        if self.monitoring.iteration_number == 1:
            self.displayCsvHeader(evolution_file)
        with open(evolution_file, 'a') as f:
            v = []
            v.append(self.monitoring.iteration_number)
            v += self.perf_indicators.getCsvLine()
            print >>f, ','.join(map(str, v))

    def displayCsvHeader(self, evolution_file):
        with open(evolution_file, 'w') as f:
            header  = ['iteration']
            header += self.perf_indicators.getCsvHeader()
            print >>f, ','.join(header)

    def loadEvolutionMonitoring(self, evolution_file):
        with open(evolution_file, 'r') as f:
            data = pd.read_csv(f, header = 0, index_col = 0)
            return data

    def plotEvolutionMonitoring(self, evolution_file, monitoring_dir):
        data = self.loadEvolutionMonitoring(evolution_file)
        if self.multiclass:
            self.plotPerfEvolution(['accuracy'], 'accuracy',
                                   data, monitoring_dir)
            self.plotPerfEvolution(['f1-micro', 'f1-macro'], 'f_micro_macro',
                                   data, monitoring_dir)
        else:
            self.plotPerfEvolution(['auc'], 'auc',
                                   data, monitoring_dir)
            self.plotPerfEvolution(['fscore', 'precision', 'recall'], 'fscore',
                                   data, monitoring_dir)

    def plotPerfEvolution(self, estimators, output_filename,
                          data, monitoring_dir):
        iterations = range(1, self.monitoring.iteration_number+1)
        plt.clf()
        for estimator in estimators:
            plot = PlotDataset(data[estimator], estimator)
            plt.plot(iterations, plot.values,
                    label = plot.label,
                    color = plot.color,
                    linewidth = plot.linewidth, marker = plot.marker)
        plt.ylim(0, 1)
        plt.xlabel('Iteration')
        plt.ylabel('Performance')
        lgd = plt.legend(bbox_to_anchor = (0., 1.02, 1., .102), loc = 3,
                ncol = 3, mode = 'expand', borderaxespad = 0.,
                fontsize = 'large')
        filename = self.outputFilename(monitoring_dir, output_filename, 'png')
        plt.savefig(filename, bbox_extra_artists=(lgd,), bbox_inches='tight')
        plt.clf()

    def outputFilename(self, monitoring_dir, name, extension):
        filename  = monitoring_dir
        filename += self.model_name + '_'
        filename += self.train_test_validation + '_'
        filename += name + '_monitoring.' + extension
        return filename

class ModelPerformanceMonitoring(object):

    def __init__(self, monitoring, model_name, validation_monitoring):
        self.monitorings = {}
        train_test_validation = ['train']
        model = monitoring.iteration.update_model.models[model_name]
        if model.cv_monitoring:
            train_test_validation.append('cv')
        if model.testing_monitoring.has_true_labels:
            train_test_validation.append('test')
        if validation_monitoring:
            train_test_validation.append('validation')
        for k in train_test_validation:
            self.monitorings[k] = TrainTestValidationPerformanceMonitoring(
                    monitoring, model_name, k)

    def generateMonitoring(self):
        for kind, monitoring in self.monitorings.iteritems():
            monitoring.generateMonitoring()

    def exportMonitoring(self, monitoring_dir, evolution_dir):
        for kind, monitoring in self.monitorings.iteritems():
            monitoring.exportMonitoring(monitoring_dir, evolution_dir)

class ModelsPerformanceMonitoring(object):

    def __init__(self, monitoring, validation_monitoring):
        self.monitoring = monitoring
        self.models_monitoring = {}
        for kind, conf in monitoring.iteration.conf.models_conf.iteritems():
            self.models_monitoring[kind] = ModelPerformanceMonitoring(monitoring, kind, validation_monitoring)

    def getOutputDirectories(self):
        monitoring_dir  = self.monitoring.iteration_dir
        monitoring_dir += 'models_performance/'
        dir_tools.createDirectory(monitoring_dir)

        evolution_dir  = self.monitoring.al_dir
        evolution_dir += 'models_performance/'
        if self.monitoring.iteration_number == 1:
            dir_tools.createDirectory(evolution_dir)

        return monitoring_dir, evolution_dir

    def generateMonitoring(self):
        for kind, monitoring in self.models_monitoring.iteritems():
            monitoring.generateMonitoring()

    def exportMonitoring(self):
        monitoring_dir, evolution_dir = self.getOutputDirectories()
        for kind, monitoring in self.models_monitoring.iteritems():
            monitoring.exportMonitoring(monitoring_dir, evolution_dir)
