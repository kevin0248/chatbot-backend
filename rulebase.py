# -*- coding: utf-8 -*-

from gensim.models import word2vec
from gensim import models

class Rule(object):
    """
    Store the concept terms of a rule, and calculate the rule similarity.
    """

    def __init__(self, rule_id, rule_term, word2vec_model):
        self.id    = rule_id
        self.term = rule_term
        self.model = word2vec_model
        self.children = []

    def __str__(self):
        res = self.term
        if self.has_child():
            res += ' with children: '
            for child in self.children:
                res += ' ' + str(child)
        return res

    def add_child(self,child_rule):
        """
        Add child rule into children list , e.g: Purchase(Parent) -> Drinks(Child).
        """
        self.children.append(child_rule)

    def has_child(self):
        return len(self.children)

    def match(self, sentence, threshold = 0):
        """
        Calculate the similarity between the input and concept term.

        Args:
            threshold: a threshold to ignore the low similarity.
            sentence : a list of words.
        Returns:
            a struct : [similarity, term_name, matchee in sentence]
        """

        max_sim = 0.0
        matchee = ""

        for word in sentence:
            try:
                sim = self.model.similarity(self.term,word)
                if sim > max_sim and sim > threshold:
                    max_sim = sim
                    matchee = word
            except Exception as e:
                print(repr(e))

        return [max_sim, self.term, matchee]

class RuleBase(object):
    """
    to store rules, and load the trained word2vec model.
    """
    def __init__(self, domain="general"):
        self.rules = {}
        self.domain = domain
        self.model = None
        self.forest_base_roots = []

    def __str__(self):
        res = "There are " + str(self.rule_amount()) + " rules in the rulebase:"
        res+= "\n-------\n"
        for key,rulebody in self.rules.items():
            res += str(rulebody) + '\n'
        return res

    def rule_amount(self):
        return len(self.rules)

    def load_rules(self,path):
        """
        Build the rulebase by loading the rules terms from the given file.
        The data format is: child term, parent term(optional)

        Args: the path of file.
        """
        assert self.model is not None, "Please load the model before any match."

        with open(path, 'r', encoding='utf-8') as input:
            for line in input:
                rule_terms = line.strip('\n').split(' ')
                new_rule = Rule(self.rule_amount(), rule_terms[0], self.model)
                self.rules[new_rule.term] = new_rule

                if len(rule_terms) > 1:
                    # this rule has parents.
                    for parent in rule_terms[1:]:
                        self.rules[parent].children.append(new_rule)
                else:
                    # is the root of classification tree.
                    self.forest_base_roots.append(new_rule)

    def load_model(self,path):
        """
        Load a trained word2vec model(binary format only).

        Args:
            path: the path of the model.
        """
        self.model = models.Word2Vec.load_word2vec_format(path,binary=True)

    def match(self, sentence, topk=1, threshold=0):
        """
        match the sentence with rules then order by similarity.

        Args:
            sentence: a list of words
            threshold: a threshold to ignore the low similarity.
        Return:
            a list holds the top k-th rules and the classification tree travel path.
        """
        assert self.model is not None, "Please load the model before any match."

        result_list  = []
        at_leaf_node = False
        term_trans   = ""
        focused_rule = self.forest_base_roots[:]

        while not at_leaf_node:

            at_leaf_node = True

            for rule in focused_rule:
                result_list.append(rule.match(sentence, threshold))

            result_list = sorted(result_list, reverse=True , key=lambda k: k[0])
            top_domain  = result_list[0][1] # get the best matcher's term.
            if self.rules[top_domain].has_child():
                result_list = []
                term_trans += top_domain+'>'
                at_leaf_node = False
                focused_rule = self.rules[top_domain].children[:]

        return [result_list,term_trans]
