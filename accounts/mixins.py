from django import forms

class TailwindFormMixin:
    """
    Mixin to apply Tailwind CSS classes to form fields automatically.
    Follows SRP (Single Responsibility Principle) by separating styling logic from form logic.
    """
    
    # Define default styles for different widget types
    # This allows for easy modification and extension (Open/Closed Principle)
    WIDGET_STYLES = {
        'TextInput': 'appearance-none block w-full px-3 py-3 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-200 ease-in-out',
        'EmailInput': 'appearance-none block w-full px-3 py-3 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-200 ease-in-out',
        'PasswordInput': 'appearance-none block w-full px-3 py-3 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-200 ease-in-out',
        'CheckboxInput': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded transition duration-150 ease-in-out',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def apply_styles(self):
        for field_name, field in self.fields.items():
            widget_type = field.widget.__class__.__name__
            
            # Apply base style if it exists for this widget type
            if widget_type in self.WIDGET_STYLES:
                existing_classes = field.widget.attrs.get('class', '')
                new_class = self.WIDGET_STYLES[widget_type]
                
                # Merge classes cleanly
                if existing_classes:
                    field.widget.attrs['class'] = f"{existing_classes} {new_class}"
                else:
                    field.widget.attrs['class'] = new_class
