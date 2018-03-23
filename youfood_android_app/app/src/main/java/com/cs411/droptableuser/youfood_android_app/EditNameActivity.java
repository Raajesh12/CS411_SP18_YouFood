package com.cs411.droptableuser.youfood_android_app;

import android.content.Intent;
import android.os.Bundle;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.support.design.widget.TextInputLayout;
import android.support.v7.app.ActionBar;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.EditText;
import android.widget.Toast;

import com.cs411.droptableuser.youfood_android_app.endpoints.UserEndpoints;
import com.cs411.droptableuser.youfood_android_app.requests.PUTUserRequest;

import butterknife.BindView;
import butterknife.ButterKnife;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Created by JunYoung on 2018. 3. 22..
 */

public class EditNameActivity extends AppCompatActivity {
    private static final String EMPTY_STRING = "";

    @BindView(R.id.toolbar_editname)
    Toolbar toolbar;
    @BindView(R.id.edittext_editname)
    EditText editTextUserName;
    @BindView(R.id.text_editname_layout_editname)
    TextInputLayout textInputLayoutUserName;
    @BindView(R.id.edittext_editpassword)
    EditText editTextPassword;
    @BindView(R.id.text_editname_layout_editpassword)
    TextInputLayout textInputLayoutPassword;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_editname);
        ButterKnife.bind(this);

        setSupportActionBar(toolbar);
        ActionBar actionBar = getSupportActionBar();
        if (actionBar != null) {
            actionBar.setTitle(EMPTY_STRING);
            actionBar.setDisplayHomeAsUpEnabled(true);
        }

        editTextUserName.setText(UtilsCache.getName());
        editTextPassword.setText(UtilsCache.getPassword());
    }

    /**
     * Initialize the contents of the Activity's standard options menu.
     *
     * @param menu The options menu in which you place your items.
     * @return TRUE for the menu to be displayed.
     */
    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.menu_editname_toolbar, menu);

        return true;
    }

    /**
     * This method is called whenever the send item is selected.
     *
     * If the username is empty, the text input layout sets an error message that will be
     * displayed below the EditText.
     *
     * If the username is valid, the method uses updateUserName() to modify the username.
     *
     * @see EditNameActivity#updateAccount(String, String)
     * @param item The menu item that was selected
     * @return Return false to allow normal menu processing to proceed, true to consume it here.
     */
    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        int id = item.getItemId();

        if (id == R.id.menu_item_send) {
            String userName = editTextUserName.getText().toString();
            String password = editTextPassword.getText().toString();
            if (userName.length() == 0) {
                textInputLayoutUserName.setError("Name cannot be updated to empty");
            }
            if(password.length() == 0) {
                textInputLayoutPassword.setError("Password cannot be updated to empty");
            }

            if((userName.length() != 0) && (password.length() != 0)) {
                updateAccount(userName, password);
            }
        }

        return super.onOptionsItemSelected(item);
    }

    /**
     * Update the user's textViewUserName.
     *
     * After updating the textViewUserName successfully, this method calls finish() to close the current activity.
     *
     * @param userName The new user textViewUserName.
     */
    private void updateAccount(final String userName, final String password) {
        Call<Void> call
                = UserEndpoints.userEndpoints.updateUser(
                new PUTUserRequest(UtilsCache.getEmail(), userName, password));

        call.enqueue(new Callback<Void>() {
            @Override
            public void onResponse(@NonNull Call<Void> call, @NonNull Response<Void> response) {
                if(response.code() == ResponseCodes.HTTP_NO_RESPONSE) {
                    UtilsCache.storeName(userName);
                    UtilsCache.storePassword(password);
                    Intent intent = new Intent();

                    setResult(response.code(), intent);
                    finish();
                } else {
                    Toast.makeText(EditNameActivity.this, "Server error", Toast.LENGTH_LONG).show();
                }
            }

            @Override
            public void onFailure(@NonNull Call<Void> call, @NonNull Throwable t) {
                Toast.makeText(EditNameActivity.this, getString(R.string.network_failed_message), Toast.LENGTH_LONG).show();
            }
        });
    }

    /**
     * This method is called whenever the user chooses to navigate Up within this activity from
     * the action bar.
     *
     * @return True, UP navigation completed successfully.
     */
    @Override
    public boolean onSupportNavigateUp() {
        finish();

        return true;
    }
}
