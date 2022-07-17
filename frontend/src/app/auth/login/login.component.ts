import { Component } from "@angular/core";
import {FormControl, Validators} from "@angular/forms";
import {Router} from "@angular/router";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  constructor( protected router: Router ) { }
  email = new FormControl('', [Validators.required, Validators.email]);
  password = new FormControl('', [Validators.required, Validators.minLength(5)]);
  hide = true;

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

  navigateRegister() {
     this.router.navigateByUrl('/auth/register').then(() => {
      window.location.reload();
    })
  }

  goLogin() {
    console.log("Login!!!")
  }
}
