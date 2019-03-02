from related_select.fields import RelatedChoiceField


class RelatedChoiceFieldWithAfter(RelatedChoiceField):
    after_label = None

    def __init__(self, related_url=None, related_dependent=None, empty_label=None, after_label=None, **kwargs):
        super(RelatedChoiceFieldWithAfter, self).__init__(related_url=related_url, related_dependent=related_dependent,
                                                          empty_label=empty_label, **kwargs)
        self.after_label = after_label

    def widget_attrs(self, widget):
        data = super(RelatedChoiceFieldWithAfter, self).widget_attrs(widget)
        data.update({'data-after-label': self.after_label})
        return

    def init_bound_field(self, obj, request_user=None):
        super(RelatedChoiceFieldWithAfter, self).init_bound_field(obj=obj, request_user=request_user)
        self.choices.append((self.after_label.replace(' ', '-').lower(), self.after_label))
