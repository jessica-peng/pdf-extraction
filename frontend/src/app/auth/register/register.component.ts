import {Component} from "@angular/core";
import {FormControl, Validators} from "@angular/forms";

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent {
  email = new FormControl('', [Validators.required, Validators.email]);
  password = new FormControl('', [Validators.required, Validators.minLength(5)]);
  confirmPassword = new FormControl('', [Validators.required]);
  hide = true;
  user: any = {};

  getEmailErrorMessage() {
    if (this.email.hasError('required')) {
      return 'You must enter a value';
    }
    return this.email.hasError('email') ? 'Not a valid email' : '';
  }

  getPasswordErrorMessage() {
    if (this.password.hasError('minlength')) {
      return 'You must enter a password limit 5 characters'
    }

    return this.password.hasError('required') ? 'You must enter a value' : '';
  }

  getConfirmPasswordErrorMessage() {
    if (this.user.password != this.user.confirmPassword) {
      return 'Password does not match the confirm password.'
    }

    return this.confirmPassword.hasError('required') ? 'You must enter a value' : '';
  }

  goRegister() {
    if (this.user.password != this.user.confirmPassword) {
      alert("Password does not match the confirm password.")
    }
    console.log("email = " + this.user.email)
    console.log("password = " + this.user.password)
    console.log("confirmPassword = " + this.user.confirmPassword)
  }
}
