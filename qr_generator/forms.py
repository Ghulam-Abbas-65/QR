from django import forms


class URLQRForm(forms.Form):
    """Form for generating QR code from URL"""
    url = forms.URLField(
        label='Enter URL',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com'
        })
    )


class FileQRForm(forms.Form):
    """Form for generating QR code from uploaded file"""
    file = forms.FileField(
        label='Upload File',
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )


class QRImageUploadForm(forms.Form):
    """Form for uploading QR code image to view analytics"""
    qr_image = forms.ImageField(
        label='Upload Your QR Code Image',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Upload the QR code image you generated to view its analytics'
    )
