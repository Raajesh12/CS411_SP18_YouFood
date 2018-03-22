package com.cs411.droptableuser.youfood_android_app;

import android.content.Context;
import android.content.Intent;
import android.support.v7.widget.RecyclerView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.RatingBar;
import android.widget.TextView;

import com.bumptech.glide.Glide;
import com.bumptech.glide.request.RequestOptions;
import com.cs411.droptableuser.youfood_android_app.responses.GETRestaurantResponse;

import java.util.List;

import butterknife.BindView;
import butterknife.ButterKnife;

// TODO: Replace the implementation with code after implementing data set.
public class RestaurantsRecyclerViewAdpater extends RecyclerView.Adapter<RestaurantsRecyclerViewAdpater.ViewHolder> {
    private static final int TEMP_NUM_ITEMS = 10;
    private static final String ZOMATO_LOGO_URL =
            "https://static2.tripoto.com/media/filter/nt/img/19307/UserPhoto/logo_unit_2_red.png";

    private List<GETRestaurantResponse> restaurants;

    public RestaurantsRecyclerViewAdpater(List<GETRestaurantResponse> restaurants) {
        this.restaurants = restaurants;
    }

    public void setData(List<GETRestaurantResponse> restaurants) {
        this.restaurants = restaurants;
        this.notifyDataSetChanged();
    }

    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_restaurant, parent, false);

        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(ViewHolder holder, int position) {
        // TODO: Resize the image with caching.
        GETRestaurantResponse restaurantObj = this.restaurants.get(position);
        Glide.with(holder.itemView.getContext())
                .load(restaurantObj.getImageURL())
                .apply(new RequestOptions().override(110, 110).fitCenter())
                .into(holder.imageViewRestaurant);
        holder.ratingBarRestaurant.setRating(3);
        holder.textViewRestaurantName.setText(restaurantObj.getName());

        String[] categories = restaurantObj.getCategories();
        StringBuilder builder = new StringBuilder();
        for(int i = 0; i < (categories.length - 1); i++) {
            builder.append(categories[i]);
            builder.append(", ");
        }
        builder.append(categories[categories.length-1]);
        holder.textViewRestaurantCuisine.setText(builder.toString());

        holder.textViewRestaurantLocation.setText(restaurantObj.getAddress());

        builder = new StringBuilder();
        if(restaurantObj.getPriceRange() != null) {
            int priceRange = Integer.parseInt(restaurantObj.getPriceRange());
            for (int i = 0; i < priceRange; i++) {
                builder.append("$");
            }

            holder.textViewRestaurantPriceRange.setText(builder.toString());
        } else {
            holder.textViewRestaurantCuisine.setText("None");
        }
    }

    // TODO: Change the total number of items after implementing data set.
    @Override
    public int getItemCount() {
        return restaurants.size();
    }

    public class ViewHolder extends RecyclerView.ViewHolder implements View.OnClickListener {
        @BindView(R.id.image_restaurant)
        ImageView imageViewRestaurant;
        @BindView(R.id.text_restaurant_name)
        TextView textViewRestaurantName;
        @BindView(R.id.text_restaurant_cuisine)
        TextView textViewRestaurantCuisine;
        @BindView(R.id.text_restaurant_location)
        TextView textViewRestaurantLocation;
        @BindView(R.id.text_restaurant_price_range)
        TextView textViewRestaurantPriceRange;
        @BindView(R.id.rating_bar_restaurant)
        RatingBar ratingBarRestaurant;

        public ViewHolder(View itemView) {
            super(itemView);
            ButterKnife.bind(this, itemView);

            itemView.setOnClickListener(this);
        }

        @Override
        public void onClick(View view) {
            final Context context = view.getContext();
            Intent detailedIntent = new Intent(context, RestaurantDetailActivity.class);

            // TODO: Add data to the intent when we have real data set.
            context.startActivity(detailedIntent);
        }
    }
}
