from hypercube_api.util import Helper
from hypercube_api.util import get_random_color
from hypercube_api.hyper_api.base import Base
from hypercube_api.utils.exceptions import ApiException


# our list here is expected to contain dictionaries, which are not hashable
def unique_list(mylist):
    res = []
    for e in mylist:
        if e not in res:
            res.append(e)
    return res


class TargetFactory:
    """
    """
    KPI_FAMILY_TARGET = "target"
    KPI_FAMILY_DESCRIPTION = "description"
    KPI_SCORE_PURITY = "Purity"
    KPI_SCORE_COVERAGE = "Coverage"
    KPI_SCORE_LIFT = "Lift"
    KPI_Z_SCORE = "Z-score"
    KPI_SCORE_AVERAGE_VALUE = "Average value"
    KPI_SCORE_STANDARD_DEVIATION = "Standard deviation"
    KPI_SCORE_SHIFT = "Shift"
    KPI_SCORE_DISCRETE = "Discrete"
    KPI_SCORE_NUMERIC = "Numeric"
    KPI_TYPE_DISCRETE_MODALITY = "Discrete variable with a modality"
    KPI_TYPE_DISCRETE = "Discrete variable"
    KPI_TYPE_CONTINUOUS = "Continuous variable"

    def __init__(self, api, project):
        self.__api = api
        self.__project = project

    @Helper.try_catch
    def create(self, variable, modality=None, scoreTypes=None):
        """
        Create one target for the given variable

        Args:
            variable (Variable): the variable defining the target
            modality (int or str or float): modality of the target if variable is discrete.
                Default is most frequent modality.
            scoreTypes (list of str): score types to be defined for the target.
                Default is [self.KPI_SCORE_PURITY, self.KPI_SCORE_COVERAGE] if variable is discrete and
                [self.KPI_SCORE_AVERAGE_VALUE] is variable is continuous.

        Returns:
            (Target): The new target
        """

        if variable.is_discrete:
            # checking if modality exists
            if modality is None:
                kpiModality = variable.top_modality
            else:
                if modality in variable.modalities:
                    kpiModality = modality
                else:
                    raise ApiException('Modality {} does not exist for variable {}'.format(modality, variable.name))
            kpiScoreTypes = set(scoreTypes or []).union({self.KPI_SCORE_PURITY, self.KPI_SCORE_COVERAGE})
        else:
            kpiModality = None
            kpiScoreTypes = set(scoreTypes or []).union({self.KPI_SCORE_AVERAGE_VALUE})

        targetData = self.__get_target_data(variable, [kpiModality, ], kpiScoreTypes)
        data = {"kpis": targetData}
        json = {'project_ID': self.__project.project_id, 'json': data}
        returned_json = self.__api.Kpi.addkpi(**json)
        if variable.is_discrete:
            targets_returned_json = [kpi for kpi in returned_json['kpis'] if kpi['kpiFamily'] == 'target' and
                                     kpi['variable'] == variable.name and kpi['modality'] == kpiModality]
        else:
            targets_returned_json = [kpi for kpi in returned_json['kpis'] if kpi['kpiFamily'] == 'target' and
                                     kpi['variable'] == variable.name]
        unique_targets_returned_json = unique_list(targets_returned_json)
        target_json = unique_targets_returned_json[0]

        return Target(self.__api, json, target_json)

    @Helper.try_catch
    def create_targets(self, variable, modalities=None, scoreTypes=None):
        """
        Create several targets for the given variable, one per modality

        Args:
            variable (Variable): variable defining the target
            modalities (list of str, float or int): modalities of the targets if the variable is discrete.
                Default is all the modalities
            scoreTypes (list of str): score types to be defined for the targets.
                Default is [self.KPI_SCORE_PURITY, self.KPI_SCORE_COVERAGE] if variable is discrete and
                [self.KPI_SCORE_AVERAGE_VALUE] is variable is continuous.
        Returns:
            (list of Target): The new target(s)
        """

        if variable.is_discrete:
            kpiModalities = modalities or variable.modalities
            kpiScoreTypes = set(scoreTypes or []).union({self.KPI_SCORE_PURITY, self.KPI_SCORE_COVERAGE})
        else:
            kpiModalities = None
            kpiScoreTypes = set(scoreTypes or []).union({self.KPI_SCORE_AVERAGE_VALUE})

        targetData = self.__get_target_data(variable, kpiModalities, kpiScoreTypes)
        data = {"kpis": targetData}
        json = {'project_ID': self.__project.project_id, 'json': data}
        returned_json = self.__api.Kpi.addkpi(**json)
        targets_returned_json = [kpi for kpi in returned_json['kpis'] if kpi['kpiFamily'] == 'target' and
                                 kpi['variable'] == variable.name]
        unique_targets_returned_json = unique_list(targets_returned_json)

        targets = []
        for target_json in unique_targets_returned_json:
            targets.append(Target(self.__api, json, target_json))

        return targets

    def __get_target_data(self, variable, modalities, kpiScoreTypes):
        targetData = []
        if variable.is_discrete:
            for modality in modalities:
                color = get_random_color()
                for scoreType in kpiScoreTypes:
                    targetData.append(
                        {
                            "color": color,
                            "projectId": self.__project.project_id,
                            "kpiName": "{} ({})".format(variable.name, modality),
                            "kpiType": self.KPI_TYPE_DISCRETE_MODALITY,
                            "kpiFamily": self.KPI_FAMILY_TARGET,
                            "output": variable.name,
                            "omodality": modality,
                            "scoreType": scoreType
                        })

        else:
            for scoreType in kpiScoreTypes:
                targetData.append(
                    {
                        "projectId": self.__project.project_id,
                        "kpiName": "{} ({})".format(variable.name, modality) if variable.is_discrete else variable.name,
                        "kpiType": self.KPI_TYPE_CONTINUOUS,
                        "kpiFamily": self.KPI_FAMILY_TARGET,
                        "output": variable.name,
                        "scoreType": scoreType
                    })
        return targetData

    @Helper.try_catch
    def create_description(self, variable):
        """
        Create a description for the given variable

        Args:
            variable (Variable): the variable defining the target

        Returns:
            (Description): The new description
        """

        targetData = [{
            "kpiFamily": self.KPI_FAMILY_DESCRIPTION,
            "kpiName": "{}_description".format(variable.name),
            "kpiType": self.KPI_TYPE_DISCRETE if variable.is_discrete else self.KPI_TYPE_CONTINUOUS,
            "output": variable.name,
            "projectId": self.__project.project_id,
            "scoreType": self.KPI_SCORE_DISCRETE if variable.is_discrete else self.KPI_SCORE_NUMERIC
        }]
        data = {"kpis": targetData}
        json = {'project_ID': self.__project.project_id, 'json': data}
        returned_json = self.__api.Kpi.addkpi(**json)
        targets_returned_json = [kpi for kpi in returned_json['kpis']
                                 if kpi['kpiFamily'] == 'description' and kpi['variable'] == variable.name]
        unique_targets_returned_json = unique_list(targets_returned_json)
        target_json = unique_targets_returned_json[0]

        return Description(self.__api, json, target_json)

    @Helper.try_catch
    def get(self, name):
        """
        Get a target or description matching the given name

        Returns:
            (KeyIndicator): The target, description or None
        """
        kis = list(filter(lambda x: x.name == name, self.filter()))
        if kis:
            return kis[0]
        return None

    @Helper.try_catch
    def get_by_id(self, id):
        """
        Get a target or description matching the given ID

        Returns:
            (KeyIndicator): The target, description or None
        """
        kis = [ki for ki in self.filter()
               if (ki.indicator_family == self.KPI_FAMILY_TARGET and id in ki.score_ids) or
                  (ki.indicator_family == self.KPI_FAMILY_DESCRIPTION and id == ki.score_id)]
        if kis:
            return kis[0]
        return None

    @Helper.try_catch
    def filter(self):
        """
        Get all targets and descriptions in this project

        Returns:
            (list of KeyIndicator): The targets and descriptions
        """
        project_id = self.__project.project_id

        json = {'project_ID': project_id}
        return list(map(lambda x: Target(self.__api, json, x)
                        if x['kpiFamily'] == self.KPI_FAMILY_TARGET
                        else Description(self.__api, json, x),
                        self.__api.Kpi.getkpisforrulebuilder(**json)))


class KeyIndicator(Base):
    """
    """
    def __init__(self, api, json_sent, json_return):
        self.__api = api
        self.__json_sent = json_sent
        self.__json_returned = json_return
        self.__type_id = self.__json_returned.get('typeId')
        self._is_deleted = False

    def __repr__(self):
        return """\n{} : {}\n""".format(
            self.__class__.__name__,
            self.name,
        ) + ("\t<! This key indicator has been deleted>\n" if self._is_deleted else "") + \
            """\t- Type : {}\n""".format(self.indicator_type)

    @property
    def _json(self):
        return self.__json_returned

    @property
    def name(self):
        return self.__json_returned.get('name')

    @property
    def project_id(self):
        return self.__json_returned.get('projectId')

    @property
    def indicator_type(self):
        """
        Get the type of this indicator : Target.KPI_TYPE_DISCRETE, Target.KPI_TYPE_CONTINUOUS
        or Target.KPI_TYPE_DISCRETE_MODALITY
        """
        return self.__json_returned.get('type')

    @property
    def indicator_family(self):
        """
        Get the family of this indicator : Target.KPI_FAMILY_TARGET or Target.KPI_FAMILY_DESCRIPTION
        """
        return self.__json_returned.get('kpiFamily')

    @property
    def variable_name(self):
        return self.__json_returned.get('variable')


class Target(KeyIndicator):
    """
    """
    def __init__(self, api, json_sent, json_return):
        self.__api = api
        self.__json_sent = json_sent
        self.__json_returned = json_return
        self.__type_id = self.__json_returned.get('typeId')
        super().__init__(api, json_sent, json_return)

    def __repr__(self):
        return super().__repr__() + """\t- Scores : {}\n\t- Color : {}\n""".format(self.scores, self.color_code)

    @property
    def color_code(self):
        return self.__json_returned.get('color')

    @property
    def modality(self):
        if self.__type_id == 0:
            return self.__json_returned.get('modality')
        else:
            return None

    @property
    def scores(self):
        return list(map(lambda x: x.get('type'), self.__json_returned.get('scores')))

    @property
    def score_ids(self):
        return list(map(lambda x: x.get('kpiId'), self.__json_returned.get('scores')))

    @Helper.try_catch
    def delete(self):
        if not self._is_deleted:
            data = {'kpis': self.score_ids}
            json = {'project_ID': self.__json_returned.get('projectId'), 'json': data}
            self.__api.Kpi.deletekpi(**json)
            self._is_deleted = True
        return self

    @Helper.try_catch
    def update(self, name):
        data = {'kpis': self.score_ids, 'newName': name}
        json = {'project_ID': self.__json_returned.get('projectId'), 'json': data}
        self.__api.Kpi.updateKpi(**json)
        return self


class Description(KeyIndicator):
    """
    """
    def __init__(self, api, json_sent, json_return):
        self.__api = api
        self.__json_sent = json_sent
        self.__json_returned = json_return
        self.__type_id = self.__json_returned.get('typeId')
        super().__init__(api, json_sent, json_return)

    def __repr__(self):
        return super().__repr__() + """\t- Score : {}\n""".format(self.score)

    @property
    def score(self):
        return self.__json_returned.get('scores')[0].get('type')

    @property
    def score_id(self):
        return self.__json_returned.get('scores')[0].get('kpiId')

    @Helper.try_catch
    def delete(self):
        if not self._is_deleted:
            data = {'kpis': [self.score_id]}
            json = {'project_ID': self.__json_returned.get('projectId'), 'json': data}
            self.__api.Kpi.deletekpi(**json)
            self._is_deleted = True
        return self

    @Helper.try_catch
    def update(self, name):
        data = {'kpis': [self.score_id], 'newName': name}
        json = {'project_ID': self.__json_returned.get('projectId'), 'json': data}
        self.__api.Kpi.updateKpi(**json)
        return self
